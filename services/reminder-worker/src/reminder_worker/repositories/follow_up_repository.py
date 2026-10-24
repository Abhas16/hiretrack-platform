import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, exists, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from hiretrack_common.db.models import Application, Company, Reminder
from hiretrack_common.domain.enums import (
    ApplicationStatus,
    ReminderCreatedBy,
    ReminderKind,
    ReminderStatus,
)


@dataclass(frozen=True)
class StaleApplication:
    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    role: str
    applied_at: datetime | None


@dataclass(frozen=True)
class NewFollowUp:
    user_id: uuid.UUID
    application_id: uuid.UUID
    message: str
    due_at: datetime


class FollowUpRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def stale_applications(self, quiet_since: datetime) -> list[StaleApplication]:
        """APPLIED applications with no status change or edit since `quiet_since`, that haven't
        had a follow-up reminder since their last status change (so a dismissed reminder isn't
        re-created every night)."""
        last_activity = func.greatest(Application.status_changed_at, Application.updated_at)
        already_reminded = exists().where(
            and_(
                Reminder.application_id == Application.id,
                Reminder.kind == ReminderKind.FOLLOW_UP,
                Reminder.created_at >= Application.status_changed_at,
            )
        )
        stmt = (
            select(
                Application.id,
                Application.user_id,
                Company.name,
                Application.role,
                Application.applied_at,
            )
            .join(Company, Company.id == Application.company_id)
            .where(
                Application.status == ApplicationStatus.APPLIED,
                last_activity < quiet_since,
                ~already_reminded,
            )
            .order_by(Application.id)
        )
        return [StaleApplication(*row) for row in self._session.execute(stmt)]

    def add_follow_ups(self, follow_ups: list[NewFollowUp]) -> int:
        """Insert in one statement; return how many were created.

        ON CONFLICT DO NOTHING hits the partial unique index "one OPEN follow-up per
        application", so two overlapping runs can't create duplicates.
        """
        if not follow_ups:
            return 0
        stmt = (
            insert(Reminder)
            .values(
                [
                    {
                        "id": uuid.uuid4(),
                        "user_id": f.user_id,
                        "application_id": f.application_id,
                        "kind": ReminderKind.FOLLOW_UP,
                        "status": ReminderStatus.OPEN,
                        "created_by": ReminderCreatedBy.WORKER,
                        "message": f.message[:500],
                        "due_at": f.due_at,
                    }
                    for f in follow_ups
                ]
            )
            .on_conflict_do_nothing()
            .returning(Reminder.id)
        )
        return len(self._session.execute(stmt).all())
