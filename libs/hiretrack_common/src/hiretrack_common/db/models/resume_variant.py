import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from hiretrack_common.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ResumeVariant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A version of the user's resume, e.g. "DevOps - Kubernetes focus", with skill tags."""

    __tablename__ = "resume_variants"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_resume_variants_user_id_name"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), default=list, server_default=text("'{}'")
    )
    summary: Mapped[str | None] = mapped_column(Text)
