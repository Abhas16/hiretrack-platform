import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hiretrack_common.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from hiretrack_common.db.models.application import Application
from hiretrack_common.domain.enums import ReminderCreatedBy, ReminderKind, ReminderStatus


class Reminder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reminders"
    __table_args__ = (
        # At most one OPEN follow-up per application. This makes the reminder-worker
        # idempotent: running it twice can't create duplicates.
        Index(
            "uq_reminders_open_follow_up",
            "application_id",
            unique=True,
            postgresql_where=text("status = 'OPEN' AND kind = 'FOLLOW_UP'"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[ReminderKind] = mapped_column(
        str_enum(ReminderKind, "reminder_kind"), default=ReminderKind.CUSTOM
    )
    status: Mapped[ReminderStatus] = mapped_column(
        str_enum(ReminderStatus, "reminder_status"), default=ReminderStatus.OPEN
    )
    created_by: Mapped[ReminderCreatedBy] = mapped_column(
        str_enum(ReminderCreatedBy, "reminder_created_by"), default=ReminderCreatedBy.USER
    )
    message: Mapped[str] = mapped_column(String(500))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    application: Mapped[Application | None] = relationship(lazy="raise")
