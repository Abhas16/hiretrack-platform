"""Create follow-up reminders for applications that have gone quiet. Safe to run any number of
times: the repository skips already-reminded applications and the DB index blocks duplicates."""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Protocol

from hiretrack_common.clock import Clock, utcnow
from reminder_worker.metrics import REMINDERS_CREATED
from reminder_worker.repositories.follow_up_repository import NewFollowUp, StaleApplication

logger = logging.getLogger(__name__)


class FollowUpStore(Protocol):
    def stale_applications(self, quiet_since: datetime) -> list[StaleApplication]: ...
    def add_follow_ups(self, follow_ups: list[NewFollowUp]) -> int: ...


class FollowUpService:
    def __init__(
        self,
        store: FollowUpStore,
        commit: Callable[[], None],
        after_days: int,
        now: Clock = utcnow,
    ) -> None:
        self._store = store
        self._commit = commit
        self._after = timedelta(days=after_days)
        self._now = now

    def run(self) -> int:
        now = self._now()
        stale = self._store.stale_applications(quiet_since=now - self._after)
        follow_ups = [
            NewFollowUp(
                user_id=app.user_id,
                application_id=app.id,
                message=_message(app, now),
                due_at=now,
            )
            for app in stale
        ]
        created = self._store.add_follow_ups(follow_ups)
        self._commit()
        REMINDERS_CREATED.inc(created)
        logger.info("follow-ups created", extra={"stale": len(stale), "reminders_created": created})
        return created


def _message(app: StaleApplication, now: datetime) -> str:
    if app.applied_at:
        days = (now - app.applied_at).days
        return f"Follow up with {app.company_name} about {app.role} (applied {days} days ago)"
    return f"Follow up with {app.company_name} about {app.role}"
