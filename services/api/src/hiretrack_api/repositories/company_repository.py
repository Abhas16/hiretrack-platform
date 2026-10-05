import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from hiretrack_api.models import Application, Company
from hiretrack_api.repositories._sql import like_pattern


class CompanyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, user_id: uuid.UUID, q: str | None = None) -> list[Company]:
        stmt = select(Company).where(Company.user_id == user_id).order_by(Company.name)
        if q:
            stmt = stmt.where(Company.name.ilike(like_pattern(q), escape="\\"))
        return list(self._session.scalars(stmt))

    def get(self, user_id: uuid.UUID, company_id: uuid.UUID) -> Company | None:
        return self._session.scalar(
            select(Company).where(Company.user_id == user_id, Company.id == company_id)
        )

    def find_by_name(self, user_id: uuid.UUID, name: str) -> Company | None:
        """Case-insensitive, so "atlassian" and "Atlassian" are the same company."""
        return self._session.scalar(
            select(Company).where(
                Company.user_id == user_id, func.lower(Company.name) == name.lower()
            )
        )

    def count_applications(self, company_id: uuid.UUID) -> int:
        stmt = select(func.count(Application.id)).where(Application.company_id == company_id)
        return self._session.scalar(stmt) or 0

    def add(self, company: Company) -> None:
        self._session.add(company)
        self._session.flush()

    def delete(self, company: Company) -> None:
        self._session.delete(company)
        self._session.flush()
