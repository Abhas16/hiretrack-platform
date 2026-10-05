import uuid

import pytest

from hiretrack_api.core.exceptions import ConflictError, NotFoundError
from hiretrack_api.interviewer.base import Evaluation, Question
from hiretrack_api.models import PracticeSession
from hiretrack_api.schemas.practice import PracticeSessionCreate, PracticeSessionRead
from hiretrack_api.services.practice_service import PracticeService
from hiretrack_common.domain.enums import PracticeStatus

from .conftest import FIXED_NOW, FakeApplicationRepository


class FakePracticeRepository:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, PracticeSession] = {}

    def list(self, user_id: uuid.UUID, limit: int) -> list[PracticeSession]:
        return [s for s in self.items.values() if s.user_id == user_id][:limit]

    def get(self, user_id: uuid.UUID, session_id: uuid.UUID) -> PracticeSession | None:
        found = self.items.get(session_id)
        return found if found and found.user_id == user_id else None

    def add(self, practice_session: PracticeSession) -> None:
        practice_session.id = uuid.uuid4()
        practice_session.created_at = FIXED_NOW
        for turn in practice_session.turns:
            turn.strengths, turn.improvements = [], []
        self.items[practice_session.id] = practice_session

    def delete(self, practice_session: PracticeSession) -> None:
        del self.items[practice_session.id]


class FakeUow:
    def __init__(self) -> None:
        self.commits = 0
        self.releases = 0

    def commit(self) -> None:
        self.commits += 1

    def release(self) -> None:
        self.releases += 1


class ScriptedInterviewer:
    """Returns fixed questions and scores, and records what it was asked."""

    name = "rule_based"

    def __init__(self, scores: list[int]) -> None:
        self.scores = scores
        self.asked: list[tuple[str, list[str], int]] = []

    def generate_questions(self, role: str, topics: list[str], count: int) -> list[Question]:
        self.asked.append((role, topics, count))
        return [
            Question(topics[i % len(topics)], f"Q{i + 1}?", ["point"], "rule_based")
            for i in range(count)
        ]

    def evaluate(self, role: str, question: Question, answer: str) -> Evaluation:
        return Evaluation(self.scores.pop(0), ["good"], ["better"], "feedback", "rule_based")


@pytest.fixture
def kit():  # type: ignore[no-untyped-def]
    repo, apps, uow = FakePracticeRepository(), FakeApplicationRepository(), FakeUow()
    interviewer = ScriptedInterviewer(scores=[6, 9, 8])
    service = PracticeService(repo, apps, interviewer, uow, now=lambda: FIXED_NOW)  # type: ignore[arg-type]
    return service, interviewer, uow


def start(service: PracticeService, user_id: uuid.UUID, **extra: object) -> PracticeSession:
    data = PracticeSessionCreate(role="Junior DevOps Engineer", question_count=3, **extra)  # type: ignore[arg-type]
    return service.create(user_id, data)


def test_start_infers_topics_and_releases_db_before_llm(kit, user_id: uuid.UUID) -> None:  # type: ignore[no-untyped-def]
    service, interviewer, uow = kit

    practice_session = start(service, user_id)

    assert interviewer.asked == [
        ("Junior DevOps Engineer", ["docker", "kubernetes", "cicd", "terraform", "behavioral"], 3)
    ]
    assert [t.position for t in practice_session.turns] == [1, 2, 3]
    assert uow.releases == 1 and uow.commits == 1


def test_explicit_topics_win_over_inferred(kit, user_id: uuid.UUID) -> None:  # type: ignore[no-untyped-def]
    service, interviewer, _ = kit
    start(service, user_id, topics=["linux", "nonsense"])
    assert interviewer.asked[0][1] == ["linux"]


def test_unknown_application_is_not_found(kit, user_id: uuid.UUID) -> None:  # type: ignore[no-untyped-def]
    service, _, _ = kit
    with pytest.raises(NotFoundError):
        start(service, user_id, application_id=uuid.uuid4())


def test_answering_all_questions_completes_with_average(kit, user_id: uuid.UUID) -> None:  # type: ignore[no-untyped-def]
    service, _, _ = kit
    practice_session = start(service, user_id)

    for answer in ("one", "two", "three"):
        practice_session = service.answer(user_id, practice_session.id, answer)

    assert practice_session.status == PracticeStatus.COMPLETED
    assert practice_session.average_score == 7.7  # (6 + 9 + 8) / 3
    assert practice_session.completed_at == FIXED_NOW
    with pytest.raises(ConflictError):
        service.answer(user_id, practice_session.id, "four")


def test_key_points_are_hidden_until_answered(kit, user_id: uuid.UUID) -> None:  # type: ignore[no-untyped-def]
    service, _, _ = kit
    practice_session = service.answer(user_id, start(service, user_id).id, "first answer")

    read = PracticeSessionRead.model_validate(practice_session)

    assert read.answered_count == 1 and read.question_count == 3
    assert read.turns[0].key_points == ["point"]
    assert read.turns[1].key_points == []


def test_other_users_session_is_not_found(kit, user_id: uuid.UUID) -> None:  # type: ignore[no-untyped-def]
    service, _, _ = kit
    practice_session = start(service, user_id)
    with pytest.raises(NotFoundError):
        service.answer(uuid.uuid4(), practice_session.id, "hi")
