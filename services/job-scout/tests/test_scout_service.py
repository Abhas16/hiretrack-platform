"""ScoutService with in-memory fakes: keyword filter, dedupe, partial failure, outbox publishing."""

import uuid
from datetime import UTC, datetime
from typing import Any

from hiretrack_common.domain.enums import JobSource
from hiretrack_common.queue import Message, QueueError
from job_scout.core.sources_config import SourcesFile
from job_scout.services.scout_service import ScoutService
from job_scout.sources.base import FetchError, JobBoard, JobPosting

NOW = datetime(2026, 10, 20, 6, 0, tzinfo=UTC)


def posting(external_id: str, title: str, slug: str = "acme") -> JobPosting:
    return JobPosting(
        source=JobSource.GREENHOUSE,
        company_slug=slug,
        company_name="Acme",
        external_id=external_id,
        title=title,
        location="Remote",
        is_remote=True,
        url=f"https://example.com/{external_id}",
        description="",
        posted_at=None,
    )


class FakeBoard:
    def __init__(self, postings: dict[str, list[JobPosting]], broken: set[str] = frozenset()):  # type: ignore[assignment]
        self.postings = postings
        self.broken = broken

    def fetch(self, slug: str, company: str) -> list[JobPosting]:
        if slug in self.broken:
            raise FetchError(f"{slug}: HTTP 404")
        return self.postings.get(slug, [])


class FakeJobStore:
    def __init__(self) -> None:
        self.rows: dict[str, uuid.UUID] = {}  # dedupe_hash -> id
        self.queued: set[uuid.UUID] = set()

    def insert_new(self, postings: list[JobPosting], now: datetime) -> int:
        new = 0
        for p in postings:
            if p.dedupe_hash not in self.rows:
                self.rows[p.dedupe_hash] = uuid.uuid4()
                new += 1
        return new

    def list_unqueued(self, limit: int) -> list[uuid.UUID]:
        return [i for i in self.rows.values() if i not in self.queued][:limit]

    def mark_queued(self, job_ids: list[uuid.UUID], now: datetime) -> None:
        self.queued.update(job_ids)


class FakeQueue:
    name = "fake"

    def __init__(self, fail: bool = False) -> None:
        self.published: list[dict[str, Any]] = []
        self.fail = fail

    def publish(self, body: dict[str, Any]) -> None:
        self.publish_many([body])

    def publish_many(self, bodies: list[dict[str, Any]]) -> None:
        if self.fail:
            raise QueueError("redis down")
        self.published.extend(bodies)

    def receive(self, max_messages: int = 10, wait_seconds: int = 10) -> list[Message]:
        return []

    def ack(self, message: Message) -> None: ...

    def ping(self) -> None: ...


def config(*slugs: str) -> SourcesFile:
    return SourcesFile.model_validate(
        {
            "defaults": {"keywords": ["devops", "sre"]},
            "sources": [{"board": "greenhouse", "slug": s, "company": s.title()} for s in slugs],
        }
    )


def service(board: JobBoard, store: FakeJobStore, queue: FakeQueue) -> ScoutService:
    return ScoutService({JobSource.GREENHOUSE: board}, store, lambda: None, queue, now=lambda: NOW)


def test_keeps_only_relevant_titles_and_publishes_them() -> None:
    board = FakeBoard(
        {"acme": [posting("1", "Senior DevOps Engineer"), posting("2", "Sales Lead")]}
    )
    store, queue = FakeJobStore(), FakeQueue()

    result = service(board, store, queue).run(config("acme"))

    assert (result.fetched, result.new, result.published) == (1, 1, 1)
    assert queue.published == [{"job_id": str(next(iter(store.rows.values())))}]
    assert result.succeeded(1)


def test_second_run_finds_nothing_new() -> None:
    board = FakeBoard({"acme": [posting("1", "SRE")]})
    store, queue = FakeJobStore(), FakeQueue()
    service(board, store, queue).run(config("acme"))

    again = service(board, store, queue).run(config("acme"))

    assert (again.fetched, again.new, again.published) == (1, 0, 0)
    assert len(queue.published) == 1


def test_one_broken_source_does_not_stop_the_others() -> None:
    board = FakeBoard({"good": [posting("1", "SRE", slug="good")]}, broken={"gone"})
    result = service(board, FakeJobStore(), FakeQueue()).run(config("gone", "good"))

    assert result.failed_sources == ["greenhouse/gone"]
    assert result.new == 1
    assert result.succeeded(2)  # partial failure is still a successful run


def test_every_source_failing_fails_the_run() -> None:
    board = FakeBoard({}, broken={"a", "b"})
    result = service(board, FakeJobStore(), FakeQueue()).run(config("a", "b"))
    assert not result.succeeded(2)


def test_queue_outage_keeps_jobs_unqueued_for_the_next_run() -> None:
    board = FakeBoard({"acme": [posting("1", "DevOps Engineer")]})
    store = FakeJobStore()

    failed = service(board, store, FakeQueue(fail=True)).run(config("acme"))
    assert failed.new == 1 and failed.published == 0
    assert not failed.succeeded(1)
    assert len(store.list_unqueued(10)) == 1  # stored, but still waiting to be published

    queue = FakeQueue()
    recovered = service(board, store, queue).run(config("acme"))
    assert recovered.new == 0 and recovered.published == 1  # the outbox caught up
    assert len(queue.published) == 1
