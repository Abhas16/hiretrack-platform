import uuid

from hiretrack_api.core.database import UnitOfWork
from hiretrack_api.core.exceptions import ConflictError, InvalidInputError, NotFoundError
from hiretrack_api.models import Company
from hiretrack_api.repositories.company_repository import CompanyRepository
from hiretrack_api.schemas.company import CompanyCreate, CompanyUpdate


class CompanyService:
    def __init__(self, companies: CompanyRepository, uow: UnitOfWork) -> None:
        self._companies = companies
        self._uow = uow

    def list(self, user_id: uuid.UUID, q: str | None) -> list[Company]:
        return self._companies.list(user_id, q)

    def get(self, user_id: uuid.UUID, company_id: uuid.UUID) -> Company:
        company = self._companies.get(user_id, company_id)
        if company is None:
            raise NotFoundError("Company not found")
        return company

    def create(self, user_id: uuid.UUID, data: CompanyCreate) -> Company:
        self._ensure_name_free(user_id, data.name)
        company = Company(user_id=user_id, **data.model_dump())
        self._companies.add(company)
        self._uow.commit()
        return company

    def update(self, user_id: uuid.UUID, company_id: uuid.UUID, data: CompanyUpdate) -> Company:
        company = self.get(user_id, company_id)
        changes = data.model_dump(exclude_unset=True)
        if "name" in changes:
            if changes["name"] is None:
                raise InvalidInputError("name cannot be null")
            self._ensure_name_free(user_id, changes["name"], ignore_id=company.id)
        for field, value in changes.items():
            setattr(company, field, value)
        self._uow.commit()
        return company

    def delete(self, user_id: uuid.UUID, company_id: uuid.UUID) -> None:
        company = self.get(user_id, company_id)
        count = self._companies.count_applications(company.id)
        if count:
            raise ConflictError(f"Company has {count} application(s); delete or move them first")
        self._companies.delete(company)
        self._uow.commit()

    def _ensure_name_free(
        self, user_id: uuid.UUID, name: str, ignore_id: uuid.UUID | None = None
    ) -> None:
        existing = self._companies.find_by_name(user_id, name)
        if existing and existing.id != ignore_id:
            raise ConflictError(f"Company '{existing.name}' already exists")
