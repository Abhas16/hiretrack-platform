import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hiretrack_common.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from hiretrack_common.db.models.application import Application
from hiretrack_common.domain.enums import InterviewKind, InterviewOutcome


class Interview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interviews"

    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    round_name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[InterviewKind] = mapped_column(
        str_enum(InterviewKind, "interview_kind"), default=InterviewKind.OTHER
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_minutes: Mapped[int | None]
    interviewer: Mapped[str | None] = mapped_column(String(200))
    outcome: Mapped[InterviewOutcome] = mapped_column(
        str_enum(InterviewOutcome, "interview_outcome"), default=InterviewOutcome.PENDING
    )
    notes: Mapped[str | None] = mapped_column(Text)

    application: Mapped[Application] = relationship(lazy="raise")
