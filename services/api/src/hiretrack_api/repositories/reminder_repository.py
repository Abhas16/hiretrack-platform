import uuid
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, contains_eager

from hiretrack_api.models import Application, Reminder
from hiretrack_common.domain.enums import ReminderStatus


class ReminderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _select(self, user_id: uuid.UUID) -> Select[tuple[Reminder]]:
        return (
            select(Reminder)
            .outerjoin(Reminder.application)
            .outerjoin(Application.company)
            .options(contains_eager(Reminder.application).contains_eager(Application.company))
            .where(Reminder.user_id == user_id)
        )

    def list(
        self,
        user_id: uuid.UUID,
        status: ReminderStatus | None,
        due_before: datetime | None,
        limit: int,
    ) -> list[Reminder]:
        stmt = self._select(user_id)
        if status:
            stmt = stmt.where(Reminder.status == status)
        if due_before:
            stmt = stmt.where(Reminder.due_at < due_before)
        stmt = stmt.order_by(Reminder.due_at, Reminder.id).limit(limit)
        return list(self._session.scalars(stmt))

    def get(self, user_id: uuid.UUID, reminder_id: uuid.UUID) -> Reminder | None:
        return self._session.scalar(self._select(user_id).where(Reminder.id == reminder_id))

    def add(self, reminder: Reminder) -> None:
        self._session.add(reminder)
        self._session.flush()

    def delete(self, reminder: Reminder) -> None:
        self._session.delete(reminder)
        self._session.flush()
