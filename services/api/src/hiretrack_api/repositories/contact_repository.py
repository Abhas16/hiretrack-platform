import uuid

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session, contains_eager

from hiretrack_api.models import Company, Contact
from hiretrack_api.repositories._sql import like_pattern


class ContactRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _select(self, user_id: uuid.UUID) -> Select[tuple[Contact]]:
        return (
            select(Contact)
            .outerjoin(Contact.company)
            .options(contains_eager(Contact.company))
            .where(Contact.user_id == user_id)
        )

    def list(
        self, user_id: uuid.UUID, company_id: uuid.UUID | None, q: str | None
    ) -> list[Contact]:
        stmt = self._select(user_id).order_by(Contact.name)
        if company_id:
            stmt = stmt.where(Contact.company_id == company_id)
        if q:
            pattern = like_pattern(q)
            stmt = stmt.where(
                or_(
                    Contact.name.ilike(pattern, escape="\\"),
                    Contact.title.ilike(pattern, escape="\\"),
                    Company.name.ilike(pattern, escape="\\"),
                )
            )
        return list(self._session.scalars(stmt))

    def get(self, user_id: uuid.UUID, contact_id: uuid.UUID) -> Contact | None:
        return self._session.scalar(self._select(user_id).where(Contact.id == contact_id))

    def add(self, contact: Contact) -> None:
        self._session.add(contact)
        self._session.flush()

    def delete(self, contact: Contact) -> None:
        self._session.delete(contact)
        self._session.flush()
