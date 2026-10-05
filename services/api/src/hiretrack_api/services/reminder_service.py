import uuid
from datetime import datetime

from hiretrack_api.core.database import UnitOfWork
from hiretrack_api.core.exceptions import InvalidInputError, NotFoundError
from hiretrack_api.models import Reminder
from hiretrack_api.repositories.application_repository import ApplicationRepository
from hiretrack_api.repositories.reminder_repository import ReminderRepository
from hiretrack_api.schemas.reminder import ReminderCreate, ReminderUpdate
from hiretrack_common.clock import Clock, utcnow
from hiretrack_common.domain.enums import ReminderCreatedBy, ReminderKind, ReminderStatus


class ReminderService:
    """User-created reminders. Follow-up reminders are created by the reminder-worker."""

    def __init__(
        self,
        reminders: ReminderRepository,
        applications: ApplicationRepository,
        uow: UnitOfWork,
        now: Clock = utcnow,
    ) -> None:
        self._reminders = reminders
        self._apps = applications
        self._uow = uow
        self._now = now

    def list(
        self,
        user_id: uuid.UUID,
        status: ReminderStatus | None,
        due_before: datetime | None,
        limit: int,
    ) -> list[Reminder]:
        return self._reminders.list(user_id, status, due_before, limit)

    def get(self, user_id: uuid.UUID, reminder_id: uuid.UUID) -> Reminder:
        reminder = self._reminders.get(user_id, reminder_id)
        if reminder is None:
            raise NotFoundError("Reminder not found")
        return reminder

    def create(self, user_id: uuid.UUID, data: ReminderCreate) -> Reminder:
        application = None
        if data.application_id is not None:
            application = self._apps.get(user_id, data.application_id)
            if application is None:
                raise NotFoundError("Application not found")
        reminder = Reminder(
            user_id=user_id,
            application_id=data.application_id,
            kind=ReminderKind.CUSTOM,
            status=ReminderStatus.OPEN,
            created_by=ReminderCreatedBy.USER,
            message=data.message,
            due_at=data.due_at,
        )
        reminder.application = application
        self._reminders.add(reminder)
        self._uow.commit()
        return reminder

    def update(self, user_id: uuid.UUID, reminder_id: uuid.UUID, data: ReminderUpdate) -> Reminder:
        reminder = self.get(user_id, reminder_id)
        changes = data.model_dump(exclude_unset=True)
        for required in ("status", "due_at", "message"):
            if required in changes and changes[required] is None:
                raise InvalidInputError(f"{required} cannot be null")

        if "status" in changes:
            reminder.status = changes["status"]
            reminder.completed_at = None if reminder.status == ReminderStatus.OPEN else self._now()
        if "due_at" in changes:
            reminder.due_at = changes["due_at"]
        if "message" in changes:
            reminder.message = changes["message"]

        self._uow.commit()
        return reminder

    def delete(self, user_id: uuid.UUID, reminder_id: uuid.UUID) -> None:
        reminder = self.get(user_id, reminder_id)
        self._reminders.delete(reminder)
        self._uow.commit()
