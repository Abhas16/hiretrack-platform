import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hiretrack_common.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from hiretrack_common.domain.enums import PracticeStatus


class PracticeSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One mock interview: a role, a set of questions, and the user's answers."""

    __tablename__ = "practice_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # Optional link to the application you're preparing for.
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"), index=True
    )
    role: Mapped[str] = mapped_column(String(200))
    topics: Mapped[list[str]] = mapped_column(
        ARRAY(String(30)), default=list, server_default=text("'{}'")
    )
    provider: Mapped[str] = mapped_column(String(20))  # who wrote the questions
    status: Mapped[PracticeStatus] = mapped_column(
        str_enum(PracticeStatus, "practice_status"), default=PracticeStatus.IN_PROGRESS
    )
    average_score: Mapped[float | None]
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    turns: Mapped[list["PracticeTurn"]] = relationship(
        lazy="raise",
        order_by="PracticeTurn.position",
        cascade="all, delete-orphan",
        back_populates="session",
    )


class PracticeTurn(UUIDPrimaryKeyMixin, Base):
    """One question in a session, and (once answered) the answer and its evaluation."""

    __tablename__ = "practice_turns"
    __table_args__ = (
        UniqueConstraint("session_id", "position", name="uq_practice_turns_session_id_position"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int]
    topic: Mapped[str] = mapped_column(String(30))
    question: Mapped[str] = mapped_column(Text)
    # What a strong answer covers. Hidden from the user until they've answered.
    key_points: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'")
    )
    answer: Mapped[str | None] = mapped_column(Text)
    score: Mapped[int | None]  # 0..10
    strengths: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'")
    )
    improvements: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'")
    )
    feedback: Mapped[str | None] = mapped_column(Text)
    evaluated_by: Mapped[str | None] = mapped_column(String(20))
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    session: Mapped[PracticeSession] = relationship(lazy="raise", back_populates="turns")
