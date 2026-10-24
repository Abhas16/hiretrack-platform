"""The normalized job shape and the interface every job-board adapter implements."""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from hiretrack_common.domain.enums import JobSource


class FetchError(Exception):
    """A board could not be read (after retries), or robots.txt forbids it."""


@dataclass(frozen=True)
class JobPosting:
    source: JobSource
    company_slug: str
    company_name: str
    external_id: str
    title: str
    location: str | None
    is_remote: bool
    url: str
    description: str
    posted_at: datetime | None

    @property
    def dedupe_hash(self) -> str:
        """Same board + company + board's own job ID = same job, even if the text changes."""
        key = f"{self.source}:{self.company_slug.lower()}:{self.external_id}"
        return hashlib.sha256(key.encode()).hexdigest()


class JobBoard(Protocol):
    def fetch(self, slug: str, company: str) -> list[JobPosting]: ...
