import uuid

from fastapi import APIRouter, status

from hiretrack_api.controllers.deps import CurrentUser, ResumeVariantServiceDep
from hiretrack_api.schemas.resume_variant import (
    ResumeVariantCreate,
    ResumeVariantRead,
    ResumeVariantUpdate,
)

router = APIRouter(prefix="/resume-variants", tags=["resume variants"])


@router.get("")
def list_variants(user: CurrentUser, service: ResumeVariantServiceDep) -> list[ResumeVariantRead]:
    return [ResumeVariantRead.model_validate(v) for v in service.list(user.id)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_variant(
    body: ResumeVariantCreate, user: CurrentUser, service: ResumeVariantServiceDep
) -> ResumeVariantRead:
    return ResumeVariantRead.model_validate(service.create(user.id, body))


@router.get("/{variant_id}")
def get_variant(
    variant_id: uuid.UUID, user: CurrentUser, service: ResumeVariantServiceDep
) -> ResumeVariantRead:
    return ResumeVariantRead.model_validate(service.get(user.id, variant_id))


@router.patch("/{variant_id}")
def update_variant(
    variant_id: uuid.UUID,
    body: ResumeVariantUpdate,
    user: CurrentUser,
    service: ResumeVariantServiceDep,
) -> ResumeVariantRead:
    return ResumeVariantRead.model_validate(service.update(user.id, variant_id, body))


@router.delete("/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(
    variant_id: uuid.UUID, user: CurrentUser, service: ResumeVariantServiceDep
) -> None:
    service.delete(user.id, variant_id)
