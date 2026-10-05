import uuid
from datetime import datetime
from typing import Any

from pydantic import Field, computed_field, model_validator

from hiretrack_api.schemas.common import ReadModel, WriteModel
from hiretrack_api.schemas.company import CompanySummary
from hiretrack_api.schemas.resume_variant import ResumeVariantSummary
from hiretrack_common.domain.enums import ApplicationSource, ApplicationStatus
from hiretrack_common.domain.status import allowed_targets


class ApplicationCreate(WriteModel):
    """Give either company_id (existing company) or company_name (found or created)."""

    company_id: uuid.UUID | None = None
    company_name: str | None = Field(default=None, min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    source: ApplicationSource = ApplicationSource.OTHER
    job_url: str | None = Field(default=None, max_length=2000)
    status: ApplicationStatus = ApplicationStatus.WISHLIST
    applied_at: datetime | None = None
    resume_variant_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _exactly_one_company_reference(self) -> "ApplicationCreate":
        if (self.company_id is None) == (self.company_name is None):
            raise ValueError("Provide exactly one of company_id or company_name")
        return self


class ApplicationUpdate(WriteModel):
    """Status is deliberately NOT here: it changes only via PATCH /applications/{id}/status,
    where the state machine is enforced. Sending "status" here is a 422."""

    company_id: uuid.UUID | None = None
    role: str | None = Field(default=None, min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    source: ApplicationSource | None = None
    job_url: str | None = Field(default=None, max_length=2000)
    applied_at: datetime | None = None
    resume_variant_id: uuid.UUID | None = None


class StatusChangeRequest(WriteModel):
    status: ApplicationStatus


class ApplicationRead(ReadModel):
    id: uuid.UUID
    company: CompanySummary
    role: str
    location: str | None
    source: ApplicationSource
    job_url: str | None
    status: ApplicationStatus
    applied_at: datetime | None
    status_changed_at: datetime
    resume_variant: ResumeVariantSummary | None
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_transitions(self) -> list[ApplicationStatus]:
        """Lets the UI enable only the moves the API will accept."""
        return allowed_targets(self.status)


class StatusHistoryRead(ReadModel):
    from_status: ApplicationStatus | None
    to_status: ApplicationStatus
    changed_at: datetime


class BoardColumn(ReadModel):
    status: ApplicationStatus
    count: int
    items: list[ApplicationRead]


class BoardRead(ReadModel):
    columns: list[BoardColumn]


class ApplicationBrief(ReadModel):
    """Small reference used inside interviews/reminders ("Atlassian · DevOps Engineer")."""

    id: uuid.UUID
    role: str
    company_name: str

    @model_validator(mode="before")
    @classmethod
    def _from_orm_application(cls, data: Any) -> Any:
        if hasattr(data, "company") and hasattr(data, "role"):
            return {"id": data.id, "role": data.role, "company_name": data.company.name}
        return data
