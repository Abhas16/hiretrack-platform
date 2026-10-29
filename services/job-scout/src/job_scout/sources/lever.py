"""Lever Postings API (public, no key): https://github.com/lever/postings-api"""

from datetime import UTC, datetime
from typing import Any

from hiretrack_common.domain.enums import JobSource
from job_scout.sources.base import FetchError, JobPosting
from job_scout.sources.http import PoliteHttpClient
from job_scout.sources.text import html_to_text, looks_remote

BASE_URL = "https://api.lever.co/v0/postings"


class LeverBoard:
    def __init__(self, http: PoliteHttpClient, max_description_chars: int) -> None:
        self._http = http
        self._max_chars = max_description_chars

    def fetch(self, slug: str, company: str) -> list[JobPosting]:
        data: Any = self._http.get_json(f"{BASE_URL}/{slug}?mode=json")
        if not isinstance(data, list):
            raise FetchError(f"lever/{slug}: unexpected response shape")
        return [self._to_posting(slug, company, job) for job in data if job.get("id")]

    def _to_posting(self, slug: str, company: str, job: dict[str, Any]) -> JobPosting:
        location = (job.get("categories") or {}).get("location")
        # The description is split into an intro plus lists ("Requirements", ...); join them.
        sections = [job.get("descriptionPlain") or ""]
        for block in job.get("lists") or []:
            sections.append(str(block.get("text", "")))
            sections.append(html_to_text(str(block.get("content", "")), self._max_chars))
        sections.append(job.get("additionalPlain") or "")
        created_ms = job.get("createdAt")
        return JobPosting(
            source=JobSource.LEVER,
            company_slug=slug,
            company_name=company,
            external_id=str(job["id"]),
            title=str(job.get("text", "")).strip(),
            location=location,
            is_remote=job.get("workplaceType") == "remote" or looks_remote(location),
            url=job.get("hostedUrl") or f"https://jobs.lever.co/{slug}/{job['id']}",
            description="\n\n".join(s for s in sections if s.strip())[: self._max_chars],
            posted_at=(
                datetime.fromtimestamp(created_ms / 1000, UTC)
                if isinstance(created_ms, int | float)
                else None
            ),
        )
