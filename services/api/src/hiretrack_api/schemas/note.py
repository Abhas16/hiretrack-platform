import uuid
from datetime import datetime

from pydantic import Field

from hiretrack_api.schemas.common import ReadModel, WriteModel


class NoteCreate(WriteModel):
    body: str = Field(min_length=1, max_length=5000)


class NoteRead(ReadModel):
    id: uuid.UUID
    application_id: uuid.UUID
    body: str
    created_at: datetime
