import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hiretrack_common.clock import utcnow
from hiretrack_common.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from hiretrack_common.db.models.company import Company
from hiretrack_common.db.models.resume_variant import ResumeVariant
from hiretrack_common.domain.enums import ApplicationSource, ApplicationStatus


class Application(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (
        Index("ix_applications_user_id_status", "user_id", "status"),
        Index("ix_applications_user_id_applied_at", "user_id", "applied_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # RESTRICT: a company with applications can't be deleted (the API answers 409).
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), index=True
    )
    role: Mapped[str] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(200))
    source: Mapped[ApplicationSource] = mapped_column(
        str_enum(ApplicationSource, "application_source"), default=ApplicationSource.OTHER
    )
    job_url: Mapped[str | None] = mapped_column(String(2000))
    status: Mapped[ApplicationStatus] = mapped_column(
        str_enum(ApplicationStatus, "application_status"), default=ApplicationStatus.WISHLIST
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resume_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resume_variants.id", ondelete="SET NULL"), index=True
    )

    # lazy="raise": forgetting to eager-load in a repository fails loudly instead of
    # silently running one extra query per row (the N+1 problem).
    company: Mapped[Company] = relationship(lazy="raise")
    resume_variant: Mapped[ResumeVariant | None] = relationship(lazy="raise")


class ApplicationStatusHistory(UUIDPrimaryKeyMixin, Base):
    """One row per status change (and one for creation, with from_status NULL).
    Powers the funnel and "average days to first interview" analytics."""

    __tablename__ = "application_status_history"

    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    from_status: Mapped[ApplicationStatus | None] = mapped_column(
        str_enum(ApplicationStatus, "from_status")
    )
    to_status: Mapped[ApplicationStatus] = mapped_column(str_enum(ApplicationStatus, "to_status"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
