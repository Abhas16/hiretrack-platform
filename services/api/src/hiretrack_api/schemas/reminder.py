import uuid
from datetime import datetime

from pydantic import Field

from hiretrack_api.schemas.application import ApplicationBrief
from hiretrack_api.schemas.common import ReadModel, WriteModel
from hiretrack_common.domain.enums import ReminderCreatedBy, ReminderKind, ReminderStatus


class ReminderCreate(WriteModel):
    application_id: uuid.UUID | None = None
    message: str = Field(min_length=1, max_length=500)
    due_at: datetime


class ReminderUpdate(WriteModel):
    """Mark done/dismissed, snooze (new due_at), or edit the message."""

    status: ReminderStatus | None = None
    due_at: datetime | None = None
    message: str | None = Field(default=None, min_length=1, max_length=500)


class ReminderRead(ReadModel):
    id: uuid.UUID
    application: ApplicationBrief | None
    kind: ReminderKind
    status: ReminderStatus
    created_by: ReminderCreatedBy
    message: str
    due_at: datetime
    completed_at: datetime | None
    created_at: datetime
