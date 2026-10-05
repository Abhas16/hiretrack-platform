import statistics
import uuid

from hiretrack_api.core.database import UnitOfWork
from hiretrack_api.core.exceptions import ConflictError, InvalidInputError, NotFoundError
from hiretrack_api.interviewer.base import Interviewer, Question
from hiretrack_api.interviewer.metrics import EVALUATIONS
from hiretrack_api.interviewer.topics import TOPICS, infer_topics, valid_topics
from hiretrack_api.models import PracticeSession, PracticeTurn
from hiretrack_api.repositories.application_repository import ApplicationRepository
from hiretrack_api.repositories.practice_repository import PracticeRepository
from hiretrack_api.schemas.practice import PracticeSessionCreate
from hiretrack_common.clock import Clock, utcnow
from hiretrack_common.domain.enums import PracticeStatus


class PracticeService:
    def __init__(
        self,
        practice: PracticeRepository,
        applications: ApplicationRepository,
        interviewer: Interviewer,
        uow: UnitOfWork,
        now: Clock = utcnow,
    ) -> None:
        self._practice = practice
        self._apps = applications
        self._interviewer = interviewer
        self._uow = uow
        self._now = now

    @property
    def provider(self) -> str:
        return self._interviewer.name

    @staticmethod
    def topics() -> dict[str, str]:
        return TOPICS

    def list(self, user_id: uuid.UUID, limit: int) -> list[PracticeSession]:
        return self._practice.list(user_id, limit)

    def get(self, user_id: uuid.UUID, session_id: uuid.UUID) -> PracticeSession:
        practice_session = self._practice.get(user_id, session_id)
        if practice_session is None:
            raise NotFoundError("Practice session not found")
        return practice_session

    def create(self, user_id: uuid.UUID, data: PracticeSessionCreate) -> PracticeSession:
        role, application_id = data.role, None
        if data.application_id is not None:
            application = self._apps.get(user_id, data.application_id)
            if application is None:
                raise NotFoundError("Application not found")
            role, application_id = role or application.role, application.id
        if not role:
            raise InvalidInputError("Provide a role or an application_id")
        topics = valid_topics(data.topics) or infer_topics(role)

        self._uow.release()  # the LLM call can take seconds: don't hold a DB connection
        questions = self._interviewer.generate_questions(role, topics, data.question_count)
        if not questions:
            raise InvalidInputError("No questions available for these topics")

        practice_session = PracticeSession(
            user_id=user_id,
            application_id=application_id,
            role=role,
            topics=topics,
            provider=questions[0].provider or self._interviewer.name,
            status=PracticeStatus.IN_PROGRESS,
        )
        practice_session.turns = [
            PracticeTurn(position=i, topic=q.topic, question=q.text, key_points=q.key_points)
            for i, q in enumerate(questions, start=1)
        ]
        self._practice.add(practice_session)
        self._uow.commit()
        return practice_session

    def answer(self, user_id: uuid.UUID, session_id: uuid.UUID, answer: str) -> PracticeSession:
        """Evaluate the answer to the current (first unanswered) question."""
        practice_session = self.get(user_id, session_id)
        turn = self._current_turn(practice_session)
        role, position = practice_session.role, turn.position
        question = Question(turn.topic, turn.question, list(turn.key_points))

        self._uow.release()  # same reason as in create()
        evaluation = self._interviewer.evaluate(role, question, answer)
        EVALUATIONS.labels(evaluation.provider or self._interviewer.name).inc()

        # Re-read: another request (double click, second tab) may have answered meanwhile.
        practice_session = self.get(user_id, session_id)
        turn = self._current_turn(practice_session)
        if turn.position != position:
            raise ConflictError("This question was already answered")

        turn.answer = answer
        turn.score = evaluation.score
        turn.strengths = evaluation.strengths
        turn.improvements = evaluation.improvements
        turn.feedback = evaluation.feedback
        turn.evaluated_by = evaluation.provider or self._interviewer.name
        turn.answered_at = self._now()

        if all(t.answer is not None for t in practice_session.turns):
            practice_session.status = PracticeStatus.COMPLETED
            practice_session.completed_at = self._now()
            scores = [t.score for t in practice_session.turns if t.score is not None]
            practice_session.average_score = round(statistics.fmean(scores), 1) if scores else None

        self._uow.commit()
        return practice_session

    def delete(self, user_id: uuid.UUID, session_id: uuid.UUID) -> None:
        self._practice.delete(self.get(user_id, session_id))
        self._uow.commit()

    @staticmethod
    def _current_turn(practice_session: PracticeSession) -> PracticeTurn:
        if practice_session.status == PracticeStatus.COMPLETED:
            raise ConflictError("This practice session is already finished")
        turn = next((t for t in practice_session.turns if t.answer is None), None)
        if turn is None:
            raise ConflictError("All questions are already answered")
        return turn
