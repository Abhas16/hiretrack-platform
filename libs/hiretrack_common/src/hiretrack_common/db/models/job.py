from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from hiretrack_common.clock import utcnow
from hiretrack_common.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from hiretrack_common.domain.enums import JobSource


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A listing fetched by job-scout. Shared by all users; matches are per user."""

    __tablename__ = "jobs"
    __table_args__ = (
        # Small partial index: only rows still waiting to be published.
        Index("ix_jobs_unqueued", "fetched_at", postgresql_where=text("queued_at IS NULL")),
    )

    source: Mapped[JobSource] = mapped_column(str_enum(JobSource, "job_source"))
    company_slug: Mapped[str] = mapped_column(String(100))  # board token from sources.yaml
    company_name: Mapped[str] = mapped_column(String(200))
    external_id: Mapped[str] = mapped_column(String(200))
    # sha256 of source + company + external_id. UNIQUE, so inserting a job twice is a no-op:
    # that is the de-duplication, and it holds even if two scout runs overlap.
    dedupe_hash: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    location: Mapped[str | None] = mapped_column(String(300))
    is_remote: Mapped[bool] = mapped_column(default=False)
    url: Mapped[str] = mapped_column(String(2000))
    description: Mapped[str] = mapped_column(Text, default="")
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # NULL until the job ID was published to the queue: a tiny "outbox". If publishing fails
    # after the insert committed, the next scout run publishes it, so no job is silently lost.
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
