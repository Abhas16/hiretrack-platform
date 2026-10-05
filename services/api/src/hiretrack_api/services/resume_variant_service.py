import uuid

from hiretrack_api.core.database import UnitOfWork
from hiretrack_api.core.exceptions import ConflictError, InvalidInputError, NotFoundError
from hiretrack_api.models import ResumeVariant
from hiretrack_api.repositories.resume_variant_repository import ResumeVariantRepository
from hiretrack_api.schemas.resume_variant import ResumeVariantCreate, ResumeVariantUpdate


def normalize_tags(tags: list[str]) -> list[str]:
    """Drop case-insensitive duplicates, keep the first spelling and the original order."""
    seen: set[str] = set()
    result = []
    for tag in tags:
        if tag.lower() not in seen:
            seen.add(tag.lower())
            result.append(tag)
    return result


class ResumeVariantService:
    def __init__(self, variants: ResumeVariantRepository, uow: UnitOfWork) -> None:
        self._variants = variants
        self._uow = uow

    def list(self, user_id: uuid.UUID) -> list[ResumeVariant]:
        return self._variants.list(user_id)

    def get(self, user_id: uuid.UUID, variant_id: uuid.UUID) -> ResumeVariant:
        variant = self._variants.get(user_id, variant_id)
        if variant is None:
            raise NotFoundError("Resume variant not found")
        return variant

    def create(self, user_id: uuid.UUID, data: ResumeVariantCreate) -> ResumeVariant:
        self._ensure_name_free(user_id, data.name)
        variant = ResumeVariant(
            user_id=user_id, name=data.name, tags=normalize_tags(data.tags), summary=data.summary
        )
        self._variants.add(variant)
        self._uow.commit()
        return variant

    def update(
        self, user_id: uuid.UUID, variant_id: uuid.UUID, data: ResumeVariantUpdate
    ) -> ResumeVariant:
        variant = self.get(user_id, variant_id)
        changes = data.model_dump(exclude_unset=True)
        if "name" in changes:
            if changes["name"] is None:
                raise InvalidInputError("name cannot be null")
            self._ensure_name_free(user_id, changes["name"], ignore_id=variant.id)
        if "tags" in changes:
            changes["tags"] = normalize_tags(changes["tags"] or [])
        for field, value in changes.items():
            setattr(variant, field, value)
        self._uow.commit()
        return variant

    def delete(self, user_id: uuid.UUID, variant_id: uuid.UUID) -> None:
        # Applications that used it keep existing; their resume_variant_id becomes NULL.
        variant = self.get(user_id, variant_id)
        self._variants.delete(variant)
        self._uow.commit()

    def _ensure_name_free(
        self, user_id: uuid.UUID, name: str, ignore_id: uuid.UUID | None = None
    ) -> None:
        existing = self._variants.find_by_name(user_id, name)
        if existing and existing.id != ignore_id:
            raise ConflictError(f"Resume variant '{existing.name}' already exists")
