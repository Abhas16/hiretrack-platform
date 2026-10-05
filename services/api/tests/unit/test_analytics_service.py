import uuid
from datetime import date, timedelta

from hiretrack_api.repositories.analytics_repository import ApplicationFacts
from hiretrack_api.services.analytics_service import AnalyticsService
from hiretrack_common.domain.enums import ApplicationSource as Src
from hiretrack_common.domain.enums import ApplicationStatus as S

from .conftest import FIXED_NOW, FakeAnalyticsRepository

USER = uuid.uuid4()
DAY = timedelta(days=1)


def fact(
    status: S,
    source: Src = Src.LINKEDIN,
    applied_days_ago: int | None = 10,
    interview_after_days: int | None = None,
    offer: bool = False,
    variant: tuple[uuid.UUID, str] | None = None,
) -> ApplicationFacts:
    applied_at = FIXED_NOW - applied_days_ago * DAY if applied_days_ago is not None else None
    first_interview_at = (
        applied_at + interview_after_days * DAY
        if applied_at is not None and interview_after_days is not None
        else None
    )
    return ApplicationFacts(
        status=status,
        source=source,
        applied_at=applied_at,
        resume_variant_id=variant[0] if variant else None,
        resume_variant_name=variant[1] if variant else None,
        first_interview_at=first_interview_at,
        reached_offer=offer,
    )


# 6 applications: 1 wishlist, 5 sent; 2 reached interview (one became an offer); 1 rejected.
FACTS = [
    fact(S.WISHLIST, applied_days_ago=None),
    fact(S.APPLIED, source=Src.REFERRAL),
    fact(S.APPLIED),
    fact(S.INTERVIEW, source=Src.REFERRAL, interview_after_days=4),
    fact(S.OFFER, source=Src.NAUKRI, interview_after_days=8, offer=True),
    fact(S.REJECTED),
]


def service(facts: list[ApplicationFacts] = FACTS) -> AnalyticsService:
    return AnalyticsService(FakeAnalyticsRepository(facts), now=lambda: FIXED_NOW)  # type: ignore[arg-type]


def test_summary() -> None:
    summary = service().summary(USER)

    assert summary.total == 6
    assert summary.wishlist == 1
    assert summary.sent == 5
    assert summary.active_pipeline == 4  # everything except OFFER and REJECTED
    assert summary.interviews_in_progress == 1
    assert summary.offers == 1
    assert summary.responded == 3  # 2 interviews + 1 rejection
    assert summary.response_rate == 0.6
    assert summary.interview_rate == 0.4
    assert summary.by_status[S.APPLIED] == 2


def test_summary_with_no_data_has_zero_rates() -> None:
    summary = service([]).summary(USER)
    assert summary.response_rate == 0.0
    assert summary.interview_rate == 0.0


def test_funnel_stages() -> None:
    stages = {s.stage: s.count for s in service().funnel(USER).stages}
    assert stages == {"Saved": 6, "Applied": 5, "Interviewed": 2, "Offer": 1}


def test_per_week_is_zero_filled_and_bucketed_by_monday() -> None:
    weeks = service().per_week(USER, weeks=3).weeks

    assert [w.week_start for w in weeks] == [
        date(2026, 9, 21),
        date(2026, 9, 28),
        date(2026, 10, 5),
    ]
    # All 5 sent applications were applied 10 days ago (Fri 25 Sep) -> week of 21 Sep.
    assert [w.count for w in weeks] == [5, 0, 0]


def test_by_source_is_sorted_by_volume() -> None:
    rows = service().by_source(USER)

    assert rows[0].source == Src.LINKEDIN
    assert rows[0].applications == 3
    referral = next(r for r in rows if r.source == Src.REFERRAL)
    assert referral.interviews == 1
    assert referral.interview_rate == 0.5


def test_by_resume_variant_groups_missing_variant_together() -> None:
    kubernetes = (uuid.uuid4(), "DevOps - Kubernetes")
    facts = [
        fact(S.INTERVIEW, interview_after_days=3, variant=kubernetes),
        fact(S.APPLIED, variant=kubernetes),
        fact(S.APPLIED),
    ]

    rows = service(facts).by_resume_variant(USER)

    assert [(r.name, r.applications, r.interview_rate) for r in rows] == [
        ("DevOps - Kubernetes", 2, 0.5),
        ("No resume variant", 1, 0.0),
    ]


def test_time_to_first_interview() -> None:
    result = service().time_to_first_interview(USER)

    assert result.sample_size == 2
    assert result.average_days == 6.0
    assert result.median_days == 6.0


def test_time_to_first_interview_without_data() -> None:
    result = service([fact(S.APPLIED)]).time_to_first_interview(USER)
    assert result.sample_size == 0
    assert result.average_days is None
