import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hiretrack_common.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from hiretrack_common.db.models.job import Job
from hiretrack_common.db.models.resume_variant import ResumeVariant
from hiretrack_common.domain.enums import MatchStatus


class MatchProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """What a user is looking for. match-scorer scores every new job against each active one."""

    __tablename__ = "match_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    # {"kubernetes": 5, "terraform": 4, ...}: skill name from config/skills.yaml -> weight 1-5
    skills: Mapped[dict[str, int]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    target_roles: Mapped[list[str]] = mapped_column(
        ARRAY(String(100)), default=list, server_default=text("'{}'")
    )
    locations: Mapped[list[str]] = mapped_column(
        ARRAY(String(100)), default=list, server_default=text("'{}'")
    )
    remote_ok: Mapped[bool] = mapped_column(default=True)
    years_experience: Mapped[int] = mapped_column(Integer, default=0)


class Match(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One job scored for one user, plus the application kit. Rows wait in the review queue."""

    __tablename__ = "matches"
    __table_args__ = (
        # The queue delivers at least once, so the scorer may see a job twice. This constraint
        # (with INSERT ... ON CONFLICT DO NOTHING) makes the second delivery a no-op.
        UniqueConstraint("user_id", "job_id", name="uq_matches_user_id_job_id"),
        Index("ix_matches_user_id_status_score", "user_id", "status", "score"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    score: Mapped[int] = mapped_column(Integer)
    matched_skills: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), default=list, server_default=text("'{}'")
    )
    gaps: Mapped[list[str]] = mapped_column(
        ARRAY(String(200)), default=list, server_default=text("'{}'")
    )
    suggested_resume_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resume_variants.id", ondelete="SET NULL")
    )
    cover_note: Mapped[str] = mapped_column(Text, default="")
    resume_bullets: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'")
    )
    kit_provider: Mapped[str] = mapped_column(String(20), default="template")
    status: Mapped[MatchStatus] = mapped_column(
        str_enum(MatchStatus, "match_status"), default=MatchStatus.NEW
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL")
    )

    job: Mapped[Job] = relationship(lazy="raise")
    suggested_resume_variant: Mapped[ResumeVariant | None] = relationship(lazy="raise")
