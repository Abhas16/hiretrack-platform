import uuid
from datetime import date

from hiretrack_api.schemas.common import ReadModel
from hiretrack_common.domain.enums import ApplicationSource, ApplicationStatus


class SummaryRead(ReadModel):
    total: int
    wishlist: int
    sent: int
    active_pipeline: int  # not yet offered or rejected
    interviews_in_progress: int
    offers: int
    rejected: int
    responded: int  # sent applications that reached interview or got rejected
    response_rate: float  # responded / sent, 0..1
    interview_rate: float  # reached interview / sent, 0..1
    by_status: dict[ApplicationStatus, int]


class WeeklyCount(ReadModel):
    week_start: date  # Monday
    count: int


class PerWeekRead(ReadModel):
    weeks: list[WeeklyCount]


class FunnelStage(ReadModel):
    stage: str
    count: int


class FunnelRead(ReadModel):
    stages: list[FunnelStage]


class SourceBreakdown(ReadModel):
    source: ApplicationSource
    applications: int
    interviews: int
    offers: int
    interview_rate: float


class VariantBreakdown(ReadModel):
    resume_variant_id: uuid.UUID | None
    name: str
    applications: int
    interviews: int
    offers: int
    interview_rate: float


class TimeToFirstInterviewRead(ReadModel):
    average_days: float | None
    median_days: float | None
    sample_size: int
