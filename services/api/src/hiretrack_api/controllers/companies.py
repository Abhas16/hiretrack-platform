import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from hiretrack_api.controllers.deps import CompanyServiceDep, CurrentUser
from hiretrack_api.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("")
def list_companies(
    user: CurrentUser,
    service: CompanyServiceDep,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> list[CompanyRead]:
    return [CompanyRead.model_validate(c) for c in service.list(user.id, q)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_company(
    body: CompanyCreate, user: CurrentUser, service: CompanyServiceDep
) -> CompanyRead:
    return CompanyRead.model_validate(service.create(user.id, body))


@router.get("/{company_id}")
def get_company(
    company_id: uuid.UUID, user: CurrentUser, service: CompanyServiceDep
) -> CompanyRead:
    return CompanyRead.model_validate(service.get(user.id, company_id))


@router.patch("/{company_id}")
def update_company(
    company_id: uuid.UUID, body: CompanyUpdate, user: CurrentUser, service: CompanyServiceDep
) -> CompanyRead:
    return CompanyRead.model_validate(service.update(user.id, company_id, body))


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={409: {"description": "Company still has applications"}},
)
def delete_company(company_id: uuid.UUID, user: CurrentUser, service: CompanyServiceDep) -> None:
    service.delete(user.id, company_id)
