import uuid
from datetime import datetime

from hiretrack_api.core.database import UnitOfWork
from hiretrack_api.core.exceptions import InvalidInputError, NotFoundError
from hiretrack_api.models import Interview
from hiretrack_api.repositories.application_repository import ApplicationRepository
from hiretrack_api.repositories.interview_repository import InterviewRepository
from hiretrack_api.schemas.interview import InterviewCreate, InterviewUpdate
from hiretrack_common.clock import Clock, utcnow
from hiretrack_common.domain.enums import InterviewOutcome


class InterviewService:
    def __init__(
        self,
        interviews: InterviewRepository,
        applications: ApplicationRepository,
        uow: UnitOfWork,
        now: Clock = utcnow,
    ) -> None:
        self._interviews = interviews
        self._apps = applications
        self._uow = uow
        self._now = now

    def list_for_application(
        self, user_id: uuid.UUID, application_id: uuid.UUID
    ) -> list[Interview]:
        if self._apps.get(user_id, application_id) is None:
            raise NotFoundError("Application not found")
        return self._interviews.list_for_application(user_id, application_id)

    def list(
        self,
        user_id: uuid.UUID,
        upcoming: bool,
        scheduled_from: datetime | None,
        scheduled_to: datetime | None,
        limit: int,
    ) -> list[Interview]:
        """upcoming=True: only pending interviews from now on (dashboard "Upcoming")."""
        outcome = None
        if upcoming:
            now = self._now()
            scheduled_from = max(scheduled_from, now) if scheduled_from else now
            outcome = InterviewOutcome.PENDING
        return self._interviews.list_for_user(user_id, scheduled_from, scheduled_to, outcome, limit)

    def get(self, user_id: uuid.UUID, interview_id: uuid.UUID) -> Interview:
        interview = self._interviews.get(user_id, interview_id)
        if interview is None:
            raise NotFoundError("Interview not found")
        return interview

    def create(
        self, user_id: uuid.UUID, application_id: uuid.UUID, data: InterviewCreate
    ) -> Interview:
        application = self._apps.get(user_id, application_id)
        if application is None:
            raise NotFoundError("Application not found")
        interview = Interview(application_id=application.id, **data.model_dump())
        interview.application = application
        self._interviews.add(interview)
        self._uow.commit()
        return interview

    def update(
        self, user_id: uuid.UUID, interview_id: uuid.UUID, data: InterviewUpdate
    ) -> Interview:
        interview = self.get(user_id, interview_id)
        changes = data.model_dump(exclude_unset=True)
        for required in ("round_name", "kind", "outcome"):
            if required in changes and changes[required] is None:
                raise InvalidInputError(f"{required} cannot be null")
        for field, value in changes.items():
            setattr(interview, field, value)
        self._uow.commit()
        return interview

    def delete(self, user_id: uuid.UUID, interview_id: uuid.UUID) -> None:
        interview = self.get(user_id, interview_id)
        self._interviews.delete(interview)
        self._uow.commit()
