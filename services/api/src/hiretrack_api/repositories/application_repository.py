import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import ColumnElement, Select, UnaryExpression, func, or_, select
from sqlalchemy.orm import Session, contains_eager, selectinload

from hiretrack_api.models import Application, ApplicationStatusHistory, Company
from hiretrack_api.repositories._sql import like_pattern
from hiretrack_common.domain.enums import ApplicationSource, ApplicationStatus


@dataclass(frozen=True)
class ApplicationFilters:
    statuses: tuple[ApplicationStatus, ...] = ()
    company_id: uuid.UUID | None = None
    source: ApplicationSource | None = None
    resume_variant_id: uuid.UUID | None = None
    q: str | None = None  # matches role, company name or location
    applied_from: datetime | None = None
    applied_to: datetime | None = None


SORTABLE_COLUMNS = {
    "updated_at": Application.updated_at,
    "created_at": Application.created_at,
    "applied_at": Application.applied_at,
    "role": Application.role,
    "status": Application.status,
}


def _order_by(sort: str) -> UnaryExpression[Any]:
    """ "-updated_at" = newest first. Unknown keys were already rejected by the controller."""
    descending = sort.startswith("-")
    column = SORTABLE_COLUMNS[sort.lstrip("-")]
    return (column.desc() if descending else column.asc()).nulls_last()


class ApplicationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _select(self) -> Select[tuple[Application]]:
        # Company is joined (needed for search + response); variant is loaded in one extra query.
        return (
            select(Application)
            .join(Application.company)
            .options(contains_eager(Application.company), selectinload(Application.resume_variant))
        )

    @staticmethod
    def _conditions(user_id: uuid.UUID, f: ApplicationFilters) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = [Application.user_id == user_id]
        if f.statuses:
            conditions.append(Application.status.in_(f.statuses))
        if f.company_id:
            conditions.append(Application.company_id == f.company_id)
        if f.source:
            conditions.append(Application.source == f.source)
        if f.resume_variant_id:
            conditions.append(Application.resume_variant_id == f.resume_variant_id)
        if f.applied_from:
            conditions.append(Application.applied_at >= f.applied_from)
        if f.applied_to:
            conditions.append(Application.applied_at < f.applied_to)
        if f.q:
            pattern = like_pattern(f.q)
            conditions.append(
                or_(
                    Application.role.ilike(pattern, escape="\\"),
                    Company.name.ilike(pattern, escape="\\"),
                    Application.location.ilike(pattern, escape="\\"),
                )
            )
        return conditions

    def search(
        self,
        user_id: uuid.UUID,
        filters: ApplicationFilters,
        sort: str = "-updated_at",
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[list[Application], int]:
        conditions = self._conditions(user_id, filters)
        total_stmt = select(func.count(Application.id)).join(Application.company).where(*conditions)
        total = self._session.scalar(total_stmt) or 0

        stmt = self._select().where(*conditions).order_by(_order_by(sort), Application.id)
        stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self._session.scalars(stmt)), total

    def get(self, user_id: uuid.UUID, application_id: uuid.UUID) -> Application | None:
        stmt = self._select().where(
            Application.user_id == user_id, Application.id == application_id
        )
        return self._session.scalar(stmt)

    def add(self, application: Application) -> None:
        self._session.add(application)
        self._session.flush()

    def delete(self, application: Application) -> None:
        self._session.delete(application)
        self._session.flush()

    def add_history(self, entry: ApplicationStatusHistory) -> None:
        self._session.add(entry)
        self._session.flush()

    def list_history(self, application_id: uuid.UUID) -> list[ApplicationStatusHistory]:
        stmt = (
            select(ApplicationStatusHistory)
            .where(ApplicationStatusHistory.application_id == application_id)
            .order_by(ApplicationStatusHistory.changed_at, ApplicationStatusHistory.id)
        )
        return list(self._session.scalars(stmt))
