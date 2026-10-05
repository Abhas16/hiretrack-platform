import uuid
from datetime import datetime

from pydantic import Field

from hiretrack_api.schemas.common import ReadModel, WriteModel


class CompanyCreate(WriteModel):
    name: str = Field(min_length=1, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    careers_url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=5000)


class CompanyUpdate(WriteModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    careers_url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=5000)


class CompanySummary(ReadModel):
    id: uuid.UUID
    name: str


class CompanyRead(ReadModel):
    id: uuid.UUID
    name: str
    website: str | None
    careers_url: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime
