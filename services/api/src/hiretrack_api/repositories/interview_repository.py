import uuid
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, contains_eager

from hiretrack_api.models import Application, Interview
from hiretrack_common.domain.enums import InterviewOutcome


class InterviewRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _select(self, user_id: uuid.UUID) -> Select[tuple[Interview]]:
        # Ownership is checked through the parent application.
        return (
            select(Interview)
            .join(Interview.application)
            .join(Application.company)
            .options(contains_eager(Interview.application).contains_eager(Application.company))
            .where(Application.user_id == user_id)
        )

    def list_for_application(
        self, user_id: uuid.UUID, application_id: uuid.UUID
    ) -> list[Interview]:
        stmt = (
            self._select(user_id)
            .where(Interview.application_id == application_id)
            .order_by(Interview.scheduled_at.asc().nulls_last(), Interview.created_at)
        )
        return list(self._session.scalars(stmt))

    def list_for_user(
        self,
        user_id: uuid.UUID,
        scheduled_from: datetime | None,
        scheduled_to: datetime | None,
        outcome: InterviewOutcome | None,
        limit: int,
    ) -> list[Interview]:
        stmt = self._select(user_id)
        if scheduled_from:
            stmt = stmt.where(Interview.scheduled_at >= scheduled_from)
        if scheduled_to:
            stmt = stmt.where(Interview.scheduled_at < scheduled_to)
        if outcome:
            stmt = stmt.where(Interview.outcome == outcome)
        stmt = stmt.order_by(Interview.scheduled_at.asc().nulls_last()).limit(limit)
        return list(self._session.scalars(stmt))

    def get(self, user_id: uuid.UUID, interview_id: uuid.UUID) -> Interview | None:
        return self._session.scalar(self._select(user_id).where(Interview.id == interview_id))

    def add(self, interview: Interview) -> None:
        self._session.add(interview)
        self._session.flush()

    def delete(self, interview: Interview) -> None:
        self._session.delete(interview)
        self._session.flush()
