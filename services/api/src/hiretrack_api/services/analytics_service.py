"""Analytics computed in Python from one row per application.

A single user has hundreds of applications, not millions, so loading compact "facts" and
computing here keeps the SQL simple and the logic unit-testable without a database.
"""

import statistics
import uuid
from collections import Counter, defaultdict
from datetime import date, timedelta

from hiretrack_api.repositories.analytics_repository import AnalyticsRepository, ApplicationFacts
from hiretrack_api.schemas.analytics import (
    FunnelRead,
    FunnelStage,
    PerWeekRead,
    SourceBreakdown,
    SummaryRead,
    TimeToFirstInterviewRead,
    VariantBreakdown,
    WeeklyCount,
)
from hiretrack_common.clock import Clock, utcnow
from hiretrack_common.domain.enums import ApplicationSource
from hiretrack_common.domain.enums import ApplicationStatus as S

NO_VARIANT_NAME = "No resume variant"


def is_sent(f: ApplicationFacts) -> bool:
    return f.applied_at is not None and f.status != S.WISHLIST


def reached_interview(f: ApplicationFacts) -> bool:
    return f.first_interview_at is not None or f.status in (S.INTERVIEW, S.OFFER) or f.reached_offer


def reached_offer(f: ApplicationFacts) -> bool:
    return f.reached_offer or f.status == S.OFFER


def responded(f: ApplicationFacts) -> bool:
    """The company replied: an interview, or a rejection."""
    return reached_interview(f) or f.status == S.REJECTED


def ratio(part: int, whole: int) -> float:
    return round(part / whole, 4) if whole else 0.0


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())  # Monday


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository, now: Clock = utcnow) -> None:
        self._repo = repository
        self._now = now

    def summary(self, user_id: uuid.UUID) -> SummaryRead:
        facts = self._repo.application_facts(user_id)
        sent = [f for f in facts if is_sent(f)]
        by_status = Counter(f.status for f in facts)
        return SummaryRead(
            total=len(facts),
            wishlist=by_status[S.WISHLIST],
            sent=len(sent),
            active_pipeline=sum(1 for f in facts if f.status not in (S.OFFER, S.REJECTED)),
            interviews_in_progress=by_status[S.INTERVIEW],
            offers=sum(1 for f in facts if reached_offer(f)),
            rejected=by_status[S.REJECTED],
            responded=sum(1 for f in sent if responded(f)),
            response_rate=ratio(sum(1 for f in sent if responded(f)), len(sent)),
            interview_rate=ratio(sum(1 for f in sent if reached_interview(f)), len(sent)),
            by_status={status: by_status[status] for status in S},
        )

    def per_week(self, user_id: uuid.UUID, weeks: int) -> PerWeekRead:
        """Applications sent per week (by applied_at, UTC), oldest first, zero-filled."""
        this_week = week_start(self._now().date())
        starts = [this_week - timedelta(weeks=i) for i in reversed(range(weeks))]
        counts = Counter(
            week_start(f.applied_at.date())
            for f in self._repo.application_facts(user_id)
            if f.applied_at is not None
        )
        return PerWeekRead(weeks=[WeeklyCount(week_start=s, count=counts[s]) for s in starts])

    def funnel(self, user_id: uuid.UUID) -> FunnelRead:
        facts = self._repo.application_facts(user_id)
        return FunnelRead(
            stages=[
                FunnelStage(stage="Saved", count=len(facts)),
                FunnelStage(stage="Applied", count=sum(1 for f in facts if f.applied_at)),
                FunnelStage(
                    stage="Interviewed", count=sum(1 for f in facts if reached_interview(f))
                ),
                FunnelStage(stage="Offer", count=sum(1 for f in facts if reached_offer(f))),
            ]
        )

    def by_source(self, user_id: uuid.UUID) -> list[SourceBreakdown]:
        groups: dict[ApplicationSource, list[ApplicationFacts]] = defaultdict(list)
        for f in self._repo.application_facts(user_id):
            groups[f.source].append(f)
        rows = [
            SourceBreakdown(
                source=source,
                applications=len(items),
                interviews=sum(1 for f in items if reached_interview(f)),
                offers=sum(1 for f in items if reached_offer(f)),
                interview_rate=self._interview_rate(items),
            )
            for source, items in groups.items()
        ]
        return sorted(rows, key=lambda r: (-r.applications, r.source))

    def by_resume_variant(self, user_id: uuid.UUID) -> list[VariantBreakdown]:
        groups: dict[tuple[uuid.UUID | None, str], list[ApplicationFacts]] = defaultdict(list)
        for f in self._repo.application_facts(user_id):
            key = (f.resume_variant_id, f.resume_variant_name or NO_VARIANT_NAME)
            groups[key].append(f)
        rows = [
            VariantBreakdown(
                resume_variant_id=variant_id,
                name=name,
                applications=len(items),
                interviews=sum(1 for f in items if reached_interview(f)),
                offers=sum(1 for f in items if reached_offer(f)),
                interview_rate=self._interview_rate(items),
            )
            for (variant_id, name), items in groups.items()
        ]
        return sorted(rows, key=lambda r: (-r.interview_rate, -r.applications, r.name))

    def time_to_first_interview(self, user_id: uuid.UUID) -> TimeToFirstInterviewRead:
        days = [
            (f.first_interview_at - f.applied_at).total_seconds() / 86400
            for f in self._repo.application_facts(user_id)
            if f.applied_at and f.first_interview_at and f.first_interview_at >= f.applied_at
        ]
        if not days:
            return TimeToFirstInterviewRead(average_days=None, median_days=None, sample_size=0)
        return TimeToFirstInterviewRead(
            average_days=round(statistics.fmean(days), 1),
            median_days=round(statistics.median(days), 1),
            sample_size=len(days),
        )

    @staticmethod
    def _interview_rate(items: list[ApplicationFacts]) -> float:
        sent = [f for f in items if is_sent(f)]
        return ratio(sum(1 for f in sent if reached_interview(f)), len(sent))
