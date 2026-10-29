"""One scout run: read every configured board, store new jobs, publish them for scoring.

Order matters (a mini "transactional outbox"):
  1. insert new jobs + COMMIT        (queued_at is NULL)
  2. publish every job with queued_at NULL to the queue
  3. set queued_at + COMMIT
If step 2 fails, the jobs stay unqueued and the NEXT run publishes them. If step 3 fails after
step 2 worked, they are published twice, which is fine: the scorer is idempotent.
"""

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from hiretrack_common.clock import Clock, utcnow
from hiretrack_common.domain.enums import JobSource
from hiretrack_common.queue import Queue, QueueError
from job_scout.core.sources_config import SourceConfig, SourcesFile
from job_scout.metrics import JOBS_FETCHED, JOBS_NEW, JOBS_PUBLISHED, SOURCE_ERRORS
from job_scout.sources.base import FetchError, JobBoard, JobPosting

logger = logging.getLogger(__name__)

PUBLISH_BATCH = 500


class JobStore(Protocol):
    """What the service needs from storage (JobRepository in production, a fake in tests)."""

    def insert_new(self, postings: list[JobPosting], now: datetime) -> int: ...
    def list_unqueued(self, limit: int) -> list[uuid.UUID]: ...
    def mark_queued(self, job_ids: list[uuid.UUID], now: datetime) -> None: ...


@dataclass
class RunResult:
    fetched: int = 0
    new: int = 0
    published: int = 0
    failed_sources: list[str] = field(default_factory=list)
    publish_error: str | None = None

    def succeeded(self, source_count: int) -> bool:
        """A run fails if publishing failed or EVERY source failed (likely our network/DNS);
        one broken company slug alone shouldn't page anyone."""
        all_failed = source_count > 0 and len(self.failed_sources) == source_count
        return self.publish_error is None and not all_failed


class ScoutService:
    def __init__(
        self,
        boards: dict[JobSource, JobBoard],
        jobs: JobStore,
        commit: Callable[[], None],
        queue: Queue,
        now: Clock = utcnow,
    ) -> None:
        self._boards = boards
        self._jobs = jobs
        self._commit = commit
        self._queue = queue
        self._now = now

    def run(self, config: SourcesFile) -> RunResult:
        result = RunResult()
        for source in config.sources:
            self._scout_one(source, config.keywords_for(source), result)
        self._publish_unqueued(result)
        return result

    def _scout_one(self, source: SourceConfig, keywords: list[str], result: RunResult) -> None:
        name = f"{source.board}/{source.slug}"
        try:
            postings = self._boards[source.job_source].fetch(source.slug, source.company)
        except FetchError as exc:
            # Keep going: one company changing boards must not stop the others.
            result.failed_sources.append(name)
            SOURCE_ERRORS.labels(source.board).inc()
            logger.warning("source failed", extra={"source": name, "error": str(exc)})
            return

        relevant = [p for p in postings if _title_matches(p.title, keywords)]
        new = self._jobs.insert_new(relevant, self._now())
        self._commit()

        result.fetched += len(relevant)
        result.new += new
        JOBS_FETCHED.labels(source.board).inc(len(relevant))
        JOBS_NEW.inc(new)
        logger.info(
            "source scouted",
            extra={"source": name, "listed": len(postings), "relevant": len(relevant), "new": new},
        )

    def _publish_unqueued(self, result: RunResult) -> None:
        while True:
            job_ids = self._jobs.list_unqueued(PUBLISH_BATCH)
            if not job_ids:
                return
            try:
                self._queue.publish_many([{"job_id": str(job_id)} for job_id in job_ids])
            except QueueError as exc:
                result.publish_error = str(exc)
                logger.error("publishing to the queue failed", extra={"error": str(exc)})
                return
            self._jobs.mark_queued(job_ids, self._now())
            self._commit()
            result.published += len(job_ids)
            JOBS_PUBLISHED.inc(len(job_ids))


def _title_matches(title: str, keywords: list[str]) -> bool:
    lowered = title.lower()
    return not keywords or any(word in lowered for word in keywords)
