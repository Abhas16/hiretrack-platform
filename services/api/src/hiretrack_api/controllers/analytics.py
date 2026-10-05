from typing import Annotated

from fastapi import APIRouter, Query

from hiretrack_api.controllers.deps import AnalyticsServiceDep, CurrentUser
from hiretrack_api.schemas.analytics import (
    FunnelRead,
    PerWeekRead,
    SourceBreakdown,
    SummaryRead,
    TimeToFirstInterviewRead,
    VariantBreakdown,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def summary(user: CurrentUser, service: AnalyticsServiceDep) -> SummaryRead:
    return service.summary(user.id)


@router.get("/per-week")
def per_week(
    user: CurrentUser,
    service: AnalyticsServiceDep,
    weeks: Annotated[int, Query(ge=1, le=52)] = 12,
) -> PerWeekRead:
    return service.per_week(user.id, weeks)


@router.get("/funnel")
def funnel(user: CurrentUser, service: AnalyticsServiceDep) -> FunnelRead:
    return service.funnel(user.id)


@router.get("/by-source")
def by_source(user: CurrentUser, service: AnalyticsServiceDep) -> list[SourceBreakdown]:
    return service.by_source(user.id)


@router.get("/by-resume-variant")
def by_resume_variant(user: CurrentUser, service: AnalyticsServiceDep) -> list[VariantBreakdown]:
    return service.by_resume_variant(user.id)


@router.get("/time-to-first-interview")
def time_to_first_interview(
    user: CurrentUser, service: AnalyticsServiceDep
) -> TimeToFirstInterviewRead:
    return service.time_to_first_interview(user.id)
