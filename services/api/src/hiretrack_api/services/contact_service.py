import uuid

from hiretrack_api.core.database import UnitOfWork
from hiretrack_api.core.exceptions import InvalidInputError, NotFoundError
from hiretrack_api.models import Company, Contact
from hiretrack_api.repositories.company_repository import CompanyRepository
from hiretrack_api.repositories.contact_repository import ContactRepository
from hiretrack_api.schemas.contact import ContactCreate, ContactUpdate


class ContactService:
    def __init__(
        self, contacts: ContactRepository, companies: CompanyRepository, uow: UnitOfWork
    ) -> None:
        self._contacts = contacts
        self._companies = companies
        self._uow = uow

    def list(
        self, user_id: uuid.UUID, company_id: uuid.UUID | None, q: str | None
    ) -> list[Contact]:
        return self._contacts.list(user_id, company_id, q)

    def get(self, user_id: uuid.UUID, contact_id: uuid.UUID) -> Contact:
        contact = self._contacts.get(user_id, contact_id)
        if contact is None:
            raise NotFoundError("Contact not found")
        return contact

    def create(self, user_id: uuid.UUID, data: ContactCreate) -> Contact:
        company = self._get_company(user_id, data.company_id)
        contact = Contact(user_id=user_id, **data.model_dump())
        contact.company = company
        self._contacts.add(contact)
        self._uow.commit()
        return contact

    def update(self, user_id: uuid.UUID, contact_id: uuid.UUID, data: ContactUpdate) -> Contact:
        contact = self.get(user_id, contact_id)
        changes = data.model_dump(exclude_unset=True)
        if "name" in changes and changes["name"] is None:
            raise InvalidInputError("name cannot be null")
        if "company_id" in changes:
            contact.company = self._get_company(user_id, changes["company_id"])
        for field, value in changes.items():
            setattr(contact, field, value)
        self._uow.commit()
        return contact

    def delete(self, user_id: uuid.UUID, contact_id: uuid.UUID) -> None:
        contact = self.get(user_id, contact_id)
        self._contacts.delete(contact)
        self._uow.commit()

    def _get_company(self, user_id: uuid.UUID, company_id: uuid.UUID | None) -> Company | None:
        if company_id is None:
            return None
        company = self._companies.get(user_id, company_id)
        if company is None:
            raise NotFoundError("Company not found")
        return company
