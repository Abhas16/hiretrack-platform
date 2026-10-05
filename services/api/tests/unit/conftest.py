"""In-memory fakes for repositories, so services can be tested without a database."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest
from pydantic import SecretStr

from hiretrack_api.core.config import ApiSettings
from hiretrack_api.models import (
    Application,
    ApplicationStatusHistory,
    Company,
    ResumeVariant,
    User,
)
from hiretrack_api.repositories.analytics_repository import ApplicationFacts
from hiretrack_api.repositories.application_repository import ApplicationFilters
from hiretrack_api.services.application_service import ApplicationService

FIXED_NOW = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)  # a Monday


def _persist(obj: Company | ResumeVariant | Application | User) -> None:
    """What a DB flush would do: assign the ID and timestamps."""
    if obj.id is None:
        obj.id = uuid.uuid4()
    if getattr(obj, "created_at", None) is None:
        obj.created_at = FIXED_NOW
    if getattr(obj, "updated_at", None) is None:
        obj.updated_at = FIXED_NOW


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


class FakeUserRepository:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, User] = {}

    def get(self, user_id: uuid.UUID) -> User | None:
        return self.items.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.items.values() if u.email == email.lower()), None)

    def add(self, user: User) -> None:
        if user.is_active is None:
            user.is_active = True
        _persist(user)
        self.items[user.id] = user


class FakeCompanyRepository:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, Company] = {}
        self.application_counts: dict[uuid.UUID, int] = {}

    def get(self, user_id: uuid.UUID, company_id: uuid.UUID) -> Company | None:
        company = self.items.get(company_id)
        return company if company and company.user_id == user_id else None

    def find_by_name(self, user_id: uuid.UUID, name: str) -> Company | None:
        return next(
            (
                c
                for c in self.items.values()
                if c.user_id == user_id and c.name.lower() == name.lower()
            ),
            None,
        )

    def count_applications(self, company_id: uuid.UUID) -> int:
        return self.application_counts.get(company_id, 0)

    def add(self, company: Company) -> None:
        _persist(company)
        self.items[company.id] = company

    def delete(self, company: Company) -> None:
        del self.items[company.id]


class FakeResumeVariantRepository:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, ResumeVariant] = {}

    def get(self, user_id: uuid.UUID, variant_id: uuid.UUID) -> ResumeVariant | None:
        variant = self.items.get(variant_id)
        return variant if variant and variant.user_id == user_id else None

    def add(self, variant: ResumeVariant) -> None:
        _persist(variant)
        self.items[variant.id] = variant


class FakeApplicationRepository:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, Application] = {}
        self.history: list[ApplicationStatusHistory] = []

    def get(self, user_id: uuid.UUID, application_id: uuid.UUID) -> Application | None:
        application = self.items.get(application_id)
        return application if application and application.user_id == user_id else None

    def search(
        self,
        user_id: uuid.UUID,
        filters: ApplicationFilters,
        sort: str = "-updated_at",
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[list[Application], int]:
        rows = [a for a in self.items.values() if a.user_id == user_id]
        if filters.statuses:
            rows = [a for a in rows if a.status in filters.statuses]
        if filters.q:
            q = filters.q.lower()
            rows = [a for a in rows if q in a.role.lower() or q in a.company.name.lower()]
        end = None if limit is None else offset + limit
        return rows[offset:end], len(rows)

    def add(self, application: Application) -> None:
        _persist(application)
        self.items[application.id] = application

    def delete(self, application: Application) -> None:
        del self.items[application.id]

    def add_history(self, entry: ApplicationStatusHistory) -> None:
        self.history.append(entry)

    def list_history(self, application_id: uuid.UUID) -> list[ApplicationStatusHistory]:
        return [h for h in self.history if h.application_id == application_id]


@dataclass
class FakeAnalyticsRepository:
    facts: list[ApplicationFacts] = field(default_factory=list)

    def application_facts(self, user_id: uuid.UUID) -> list[ApplicationFacts]:
        return self.facts


@dataclass
class AppServiceKit:
    service: ApplicationService
    apps: FakeApplicationRepository
    companies: FakeCompanyRepository
    variants: FakeResumeVariantRepository
    uow: FakeUnitOfWork


@pytest.fixture
def kit() -> AppServiceKit:
    apps = FakeApplicationRepository()
    companies = FakeCompanyRepository()
    variants = FakeResumeVariantRepository()
    uow = FakeUnitOfWork()
    service = ApplicationService(apps, companies, variants, uow, now=lambda: FIXED_NOW)  # type: ignore[arg-type]
    return AppServiceKit(service, apps, companies, variants, uow)


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def api_settings() -> ApiSettings:
    """Settings for app-level tests that never touch a database (port 1 = nothing listening)."""
    return ApiSettings(
        db_password=SecretStr("unused"),
        db_port=1,
        db_connect_timeout_seconds=1,
        db_sslmode="disable",
        jwt_secret=SecretStr("unit-test-secret-0123456789abcdefghij"),
        app_env="test",
        log_format="console",
    )
