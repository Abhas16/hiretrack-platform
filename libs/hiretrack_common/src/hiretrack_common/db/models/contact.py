import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hiretrack_common.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from hiretrack_common.db.models.company import Company


class Contact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A person you talk to during the search: recruiter, referrer, hiring manager."""

    __tablename__ = "contacts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    title: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(254))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)

    company: Mapped[Company | None] = relationship(lazy="raise")
