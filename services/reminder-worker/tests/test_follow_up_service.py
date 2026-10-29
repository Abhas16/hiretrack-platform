import uuid
from datetime import UTC, datetime, timedelta

from reminder_worker.repositories.follow_up_repository import NewFollowUp, StaleApplication
from reminder_worker.services.follow_up_service import FollowUpService

NOW = datetime(2026, 10, 20, 3, 30, tzinfo=UTC)


class FakeStore:
    def __init__(self, stale: list[StaleApplication]) -> None:
        self.stale = stale
        self.quiet_since: datetime | None = None
        self.added: list[NewFollowUp] = []

    def stale_applications(self, quiet_since: datetime) -> list[StaleApplication]:
        self.quiet_since = quiet_since
        return self.stale

    def add_follow_ups(self, follow_ups: list[NewFollowUp]) -> int:
        self.added.extend(follow_ups)
        return len(follow_ups)


def test_creates_one_follow_up_per_stale_application() -> None:
    app = StaleApplication(uuid.uuid4(), uuid.uuid4(), "Swiggy", "SRE", NOW - timedelta(days=9))
    store = FakeStore([app])
    commits: list[bool] = []

    created = FollowUpService(store, lambda: commits.append(True), 7, now=lambda: NOW).run()

    assert created == 1
    assert store.quiet_since == NOW - timedelta(days=7)
    [follow_up] = store.added
    assert follow_up.message == "Follow up with Swiggy about SRE (applied 9 days ago)"
    assert follow_up.due_at == NOW
    assert commits == [True]


def test_nothing_stale_still_commits_cleanly() -> None:
    store = FakeStore([])
    assert FollowUpService(store, lambda: None, 7, now=lambda: NOW).run() == 0
