import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from hiretrack_common.db.models import Job
from job_scout.sources.base import JobPosting


class JobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def insert_new(self, postings: list[JobPosting], now: datetime) -> int:
        """Insert postings not stored yet; return how many were new.

        ON CONFLICT DO NOTHING on the unique dedupe_hash: the database decides what is new,
        in one statement, so even two overlapping scout runs can't store a job twice.
        """
        if not postings:
            return 0
        rows = [
            {
                "id": uuid.uuid4(),
                "source": p.source,
                "company_slug": p.company_slug,
                "company_name": p.company_name,
                "external_id": p.external_id,
                "dedupe_hash": p.dedupe_hash,
                "title": p.title[:300],
                "location": p.location[:300] if p.location else None,
                "is_remote": p.is_remote,
                "url": p.url[:2000],
                "description": p.description,
                "posted_at": p.posted_at,
                "fetched_at": now,
            }
            for p in _unique(postings)
        ]
        stmt = (
            insert(Job)
            .values(rows)
            .on_conflict_do_nothing(index_elements=[Job.dedupe_hash])
            .returning(Job.id)
        )
        return len(self._session.execute(stmt).all())

    def list_unqueued(self, limit: int) -> list[uuid.UUID]:
        stmt = select(Job.id).where(Job.queued_at.is_(None)).order_by(Job.fetched_at).limit(limit)
        return list(self._session.scalars(stmt))

    def mark_queued(self, job_ids: list[uuid.UUID], now: datetime) -> None:
        if job_ids:
            self._session.execute(update(Job).where(Job.id.in_(job_ids)).values(queued_at=now))


def _unique(postings: list[JobPosting]) -> list[JobPosting]:
    """A board can list the same job twice in one response; one INSERT can't contain a
    duplicate conflict key, so drop repeats first."""
    seen: dict[str, JobPosting] = {}
    for posting in postings:
        seen.setdefault(posting.dedupe_hash, posting)
    return list(seen.values())
