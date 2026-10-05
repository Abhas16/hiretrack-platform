import uuid
from datetime import datetime

from pydantic import Field

from hiretrack_api.schemas.application import ApplicationBrief
from hiretrack_api.schemas.common import ReadModel, WriteModel
from hiretrack_common.domain.enums import InterviewKind, InterviewOutcome


class InterviewCreate(WriteModel):
    round_name: str = Field(min_length=1, max_length=120)
    kind: InterviewKind = InterviewKind.OTHER
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=600)
    interviewer: str | None = Field(default=None, max_length=200)
    outcome: InterviewOutcome = InterviewOutcome.PENDING
    notes: str | None = Field(default=None, max_length=5000)


class InterviewUpdate(WriteModel):
    round_name: str | None = Field(default=None, min_length=1, max_length=120)
    kind: InterviewKind | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=600)
    interviewer: str | None = Field(default=None, max_length=200)
    outcome: InterviewOutcome | None = None
    notes: str | None = Field(default=None, max_length=5000)


class InterviewRead(ReadModel):
    id: uuid.UUID
    application: ApplicationBrief
    round_name: str
    kind: InterviewKind
    scheduled_at: datetime | None
    duration_minutes: int | None
    interviewer: str | None
    outcome: InterviewOutcome
    notes: str | None
    created_at: datetime
    updated_at: datetime
