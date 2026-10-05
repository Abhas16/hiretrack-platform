import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from hiretrack_api.models import Application, ApplicationStatusHistory, ResumeVariant
from hiretrack_common.domain.enums import ApplicationSource, ApplicationStatus


@dataclass(frozen=True)
class ApplicationFacts:
    """Everything analytics needs about one application, in one row."""

    status: ApplicationStatus
    source: ApplicationSource
    applied_at: datetime | None
    resume_variant_id: uuid.UUID | None
    resume_variant_name: str | None
    first_interview_at: datetime | None  # first time it entered INTERVIEW (from history)
    reached_offer: bool


class AnalyticsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def application_facts(self, user_id: uuid.UUID) -> list[ApplicationFacts]:
        history = ApplicationStatusHistory
        per_application = (
            select(
                history.application_id,
                func.min(history.changed_at)
                .filter(history.to_status == ApplicationStatus.INTERVIEW)
                .label("first_interview_at"),
                func.bool_or(history.to_status == ApplicationStatus.OFFER).label("reached_offer"),
            )
            .group_by(history.application_id)
            .subquery()
        )
        stmt = (
            select(
                Application.status,
                Application.source,
                Application.applied_at,
                Application.resume_variant_id,
                ResumeVariant.name,
                per_application.c.first_interview_at,
                per_application.c.reached_offer,
            )
            .outerjoin(ResumeVariant, ResumeVariant.id == Application.resume_variant_id)
            .outerjoin(per_application, per_application.c.application_id == Application.id)
            .where(Application.user_id == user_id)
        )
        return [
            ApplicationFacts(
                status=row[0],
                source=row[1],
                applied_at=row[2],
                resume_variant_id=row[3],
                resume_variant_name=row[4],
                first_interview_at=row[5],
                reached_offer=bool(row[6]),
            )
            for row in self._session.execute(stmt)
        ]
