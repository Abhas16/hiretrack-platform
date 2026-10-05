import uuid
from datetime import datetime
from typing import Annotated

from pydantic import Field, StringConstraints

from hiretrack_api.schemas.common import ReadModel, WriteModel

Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class ResumeVariantCreate(WriteModel):
    name: str = Field(min_length=1, max_length=120)
    tags: list[Tag] = Field(default_factory=list, max_length=50)
    summary: str | None = Field(default=None, max_length=5000)


class ResumeVariantUpdate(WriteModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    tags: list[Tag] | None = Field(default=None, max_length=50)
    summary: str | None = Field(default=None, max_length=5000)


class ResumeVariantSummary(ReadModel):
    id: uuid.UUID
    name: str


class ResumeVariantRead(ReadModel):
    id: uuid.UUID
    name: str
    tags: list[str]
    summary: str | None
    created_at: datetime
    updated_at: datetime
