import csv
import io
import uuid
from dataclasses import dataclass

from hiretrack_api.core.database import UnitOfWork
from hiretrack_api.core.exceptions import (
    InvalidInputError,
    InvalidStatusTransitionError,
    NotFoundError,
)
from hiretrack_api.models import Application, ApplicationStatusHistory, Company, ResumeVariant
from hiretrack_api.repositories.application_repository import (
    ApplicationFilters,
    ApplicationRepository,
)
from hiretrack_api.repositories.company_repository import CompanyRepository
from hiretrack_api.repositories.resume_variant_repository import ResumeVariantRepository
from hiretrack_api.schemas.application import ApplicationCreate, ApplicationUpdate
from hiretrack_common.clock import Clock, utcnow
from hiretrack_common.domain.enums import ApplicationStatus
from hiretrack_common.domain.status import SENT_STATUSES, STATUS_ORDER, can_transition

CSV_COLUMNS = [
    "company",
    "role",
    "location",
    "source",
    "status",
    "applied_at",
    "job_url",
    "resume_variant",
    "created_at",
    "updated_at",
]


def csv_safe(value: object) -> str:
    """Stop CSV formula injection: Excel runs cells starting with = + - @ as formulas."""
    text = "" if value is None else str(value)
    return f"'{text}" if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


@dataclass(frozen=True)
class BoardColumnData:
    status: ApplicationStatus
    items: list[Application]


class ApplicationService:
    def __init__(
        self,
        applications: ApplicationRepository,
        companies: CompanyRepository,
        variants: ResumeVariantRepository,
        uow: UnitOfWork,
        now: Clock = utcnow,
    ) -> None:
        self._apps = applications
        self._companies = companies
        self._variants = variants
        self._uow = uow
        self._now = now

    # ---- reads -------------------------------------------------------------------------
    def get(self, user_id: uuid.UUID, application_id: uuid.UUID) -> Application:
        application = self._apps.get(user_id, application_id)
        if application is None:
            # 404 (not 403) for other users' data, so IDs can't be probed.
            raise NotFoundError("Application not found")
        return application

    def search(
        self,
        user_id: uuid.UUID,
        filters: ApplicationFilters,
        sort: str,
        page: int,
        page_size: int,
    ) -> tuple[list[Application], int]:
        return self._apps.search(
            user_id, filters, sort=sort, offset=(page - 1) * page_size, limit=page_size
        )

    def board(self, user_id: uuid.UUID, q: str | None) -> list[BoardColumnData]:
        items, _ = self._apps.search(user_id, ApplicationFilters(q=q), sort="-updated_at")
        return [
            BoardColumnData(status=status, items=[a for a in items if a.status == status])
            for status in STATUS_ORDER
        ]

    def history(
        self, user_id: uuid.UUID, application_id: uuid.UUID
    ) -> list[ApplicationStatusHistory]:
        application = self.get(user_id, application_id)
        return self._apps.list_history(application.id)

    def export_csv(self, user_id: uuid.UUID, filters: ApplicationFilters) -> str:
        items, _ = self._apps.search(user_id, filters, sort="-updated_at")
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(CSV_COLUMNS)
        for a in items:
            writer.writerow(
                csv_safe(value)
                for value in (
                    a.company.name,
                    a.role,
                    a.location,
                    a.source,
                    a.status,
                    a.applied_at.isoformat() if a.applied_at else None,
                    a.job_url,
                    a.resume_variant.name if a.resume_variant else None,
                    a.created_at.isoformat(),
                    a.updated_at.isoformat(),
                )
            )
        return buffer.getvalue()

    # ---- writes ------------------------------------------------------------------------
    def create(self, user_id: uuid.UUID, data: ApplicationCreate) -> Application:
        company = self._resolve_company(user_id, data.company_id, data.company_name)
        variant = self._get_variant(user_id, data.resume_variant_id)
        now = self._now()

        applied_at = data.applied_at
        if applied_at is None and data.status in SENT_STATUSES:
            applied_at = now

        application = Application(
            user_id=user_id,
            company_id=company.id,
            company=company,
            role=data.role,
            location=data.location,
            source=data.source,
            job_url=data.job_url,
            status=data.status,
            applied_at=applied_at,
            status_changed_at=now,
            resume_variant_id=variant.id if variant else None,
            resume_variant=variant,
        )
        self._apps.add(application)
        self._apps.add_history(
            ApplicationStatusHistory(
                application_id=application.id,
                from_status=None,
                to_status=application.status,
                changed_at=now,
            )
        )
        self._uow.commit()
        return application

    def update(
        self, user_id: uuid.UUID, application_id: uuid.UUID, data: ApplicationUpdate
    ) -> Application:
        application = self.get(user_id, application_id)
        changes = data.model_dump(exclude_unset=True)

        for required in ("role", "source", "company_id"):
            if required in changes and changes[required] is None:
                raise InvalidInputError(f"{required} cannot be null")

        if "company_id" in changes:
            company = self._resolve_company(user_id, changes.pop("company_id"), None)
            application.company_id = company.id
            application.company = company
        if "resume_variant_id" in changes:
            variant = self._get_variant(user_id, changes.pop("resume_variant_id"))
            application.resume_variant_id = variant.id if variant else None
            application.resume_variant = variant
        for field, value in changes.items():
            setattr(application, field, value)

        self._uow.commit()
        return application

    def change_status(
        self, user_id: uuid.UUID, application_id: uuid.UUID, target: ApplicationStatus
    ) -> Application:
        application = self.get(user_id, application_id)
        if not can_transition(application.status, target):
            raise InvalidStatusTransitionError(application.status, target)

        now = self._now()
        self._apps.add_history(
            ApplicationStatusHistory(
                application_id=application.id,
                from_status=application.status,
                to_status=target,
                changed_at=now,
            )
        )
        application.status = target
        application.status_changed_at = now
        if target == ApplicationStatus.APPLIED and application.applied_at is None:
            application.applied_at = now

        self._uow.commit()
        return application

    def delete(self, user_id: uuid.UUID, application_id: uuid.UUID) -> None:
        application = self.get(user_id, application_id)
        self._apps.delete(application)
        self._uow.commit()

    # ---- helpers -----------------------------------------------------------------------
    def _resolve_company(
        self, user_id: uuid.UUID, company_id: uuid.UUID | None, company_name: str | None
    ) -> Company:
        if company_id is not None:
            company = self._companies.get(user_id, company_id)
            if company is None:
                raise NotFoundError("Company not found")
            return company
        if not company_name:  # ApplicationCreate's validator already guarantees one of the two
            raise InvalidInputError("company_id or company_name is required")
        existing = self._companies.find_by_name(user_id, company_name)
        if existing:
            return existing
        company = Company(user_id=user_id, name=company_name)
        self._companies.add(company)
        return company

    def _get_variant(
        self, user_id: uuid.UUID, variant_id: uuid.UUID | None
    ) -> ResumeVariant | None:
        if variant_id is None:
            return None
        variant = self._variants.get(user_id, variant_id)
        if variant is None:
            raise NotFoundError("Resume variant not found")
        return variant
