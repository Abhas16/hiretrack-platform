import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from hiretrack_api.controllers.deps import ContactServiceDep, CurrentUser
from hiretrack_api.schemas.contact import ContactCreate, ContactRead, ContactUpdate

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("")
def list_contacts(
    user: CurrentUser,
    service: ContactServiceDep,
    company_id: uuid.UUID | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> list[ContactRead]:
    return [ContactRead.model_validate(c) for c in service.list(user.id, company_id, q)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_contact(
    body: ContactCreate, user: CurrentUser, service: ContactServiceDep
) -> ContactRead:
    return ContactRead.model_validate(service.create(user.id, body))


@router.get("/{contact_id}")
def get_contact(
    contact_id: uuid.UUID, user: CurrentUser, service: ContactServiceDep
) -> ContactRead:
    return ContactRead.model_validate(service.get(user.id, contact_id))


@router.patch("/{contact_id}")
def update_contact(
    contact_id: uuid.UUID, body: ContactUpdate, user: CurrentUser, service: ContactServiceDep
) -> ContactRead:
    return ContactRead.model_validate(service.update(user.id, contact_id, body))


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: uuid.UUID, user: CurrentUser, service: ContactServiceDep) -> None:
    service.delete(user.id, contact_id)
