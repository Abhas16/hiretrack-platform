import uuid
from datetime import datetime
from typing import Annotated

from pydantic import Field, StringConstraints, field_validator

from hiretrack_api.schemas.application import ApplicationRead
from hiretrack_api.schemas.common import ReadModel, WriteModel
from hiretrack_api.schemas.resume_variant import ResumeVariantSummary
from hiretrack_common.domain.enums import JobSource, MatchStatus


class JobRead(ReadModel):
    id: uuid.UUID
    source: JobSource
    company_name: str
    title: str
    location: str | None
    is_remote: bool
    url: str
    posted_at: datetime | None


class JobDetail(JobRead):
    description: str


class MatchRead(ReadModel):
    """One card in the review queue."""

    id: uuid.UUID
    job: JobRead
    score: int
    matched_skills: list[str]
    gaps: list[str]
    suggested_resume_variant: ResumeVariantSummary | None
    cover_note: str
    resume_bullets: list[str]
    kit_provider: str
    status: MatchStatus
    decided_at: datetime | None
    application_id: uuid.UUID | None
    created_at: datetime


class MatchDetail(MatchRead):
    job: JobDetail


class ApproveResponse(ReadModel):
    """The UI opens job_url in a new tab: the user submits the application themselves."""

    match: MatchRead
    application: ApplicationRead
    job_url: str


# ---- match profile -------------------------------------------------------------------------
SkillName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class MatchProfileUpdate(WriteModel):
    is_active: bool = True
    skills: dict[SkillName, Annotated[int, Field(ge=1, le=5)]] = Field(max_length=60)
    target_roles: list[ShortText] = Field(default_factory=list, max_length=10)
    locations: list[ShortText] = Field(default_factory=list, max_length=10)
    remote_ok: bool = True
    years_experience: int = Field(default=0, ge=0, le=50)

    @field_validator("skills")
    @classmethod
    def _lower_case_names(cls, skills: dict[str, int]) -> dict[str, int]:
        return {name.lower(): weight for name, weight in skills.items()}


class MatchProfileRead(ReadModel):
    exists: bool  # False = nothing saved yet; the UI shows the setup form
    is_active: bool
    skills: dict[str, int]
    target_roles: list[str]
    locations: list[str]
    remote_ok: bool
    years_experience: int
    updated_at: datetime | None


class SkillListRead(ReadModel):
    skills: list[str]
