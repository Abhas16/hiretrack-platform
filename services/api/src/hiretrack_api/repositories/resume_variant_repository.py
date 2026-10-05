import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from hiretrack_api.models import ResumeVariant


class ResumeVariantRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, user_id: uuid.UUID) -> list[ResumeVariant]:
        stmt = (
            select(ResumeVariant)
            .where(ResumeVariant.user_id == user_id)
            .order_by(ResumeVariant.name)
        )
        return list(self._session.scalars(stmt))

    def get(self, user_id: uuid.UUID, variant_id: uuid.UUID) -> ResumeVariant | None:
        return self._session.scalar(
            select(ResumeVariant).where(
                ResumeVariant.user_id == user_id, ResumeVariant.id == variant_id
            )
        )

    def find_by_name(self, user_id: uuid.UUID, name: str) -> ResumeVariant | None:
        return self._session.scalar(
            select(ResumeVariant).where(
                ResumeVariant.user_id == user_id, func.lower(ResumeVariant.name) == name.lower()
            )
        )

    def add(self, variant: ResumeVariant) -> None:
        self._session.add(variant)
        self._session.flush()

    def delete(self, variant: ResumeVariant) -> None:
        self._session.delete(variant)
        self._session.flush()
