import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from hiretrack_api.schemas.common import ReadModel, WriteModel
from hiretrack_api.schemas.company import CompanySummary


class ContactCreate(WriteModel):
    name: str = Field(min_length=1, max_length=200)
    title: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    linkedin_url: str | None = Field(default=None, max_length=500)
    company_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=5000)


class ContactUpdate(WriteModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    title: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    linkedin_url: str | None = Field(default=None, max_length=500)
    company_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=5000)


class ContactRead(ReadModel):
    id: uuid.UUID
    name: str
    title: str | None
    email: str | None
    linkedin_url: str | None
    company: CompanySummary | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
