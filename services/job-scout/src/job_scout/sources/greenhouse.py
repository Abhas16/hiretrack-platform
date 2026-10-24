"""Greenhouse Job Board API (public, no key): https://developers.greenhouse.io/job-board.html"""

from typing import Any

from hiretrack_common.domain.enums import JobSource
from job_scout.sources.base import FetchError, JobPosting
from job_scout.sources.http import PoliteHttpClient
from job_scout.sources.text import html_to_text, looks_remote, parse_iso

BASE_URL = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseBoard:
    def __init__(self, http: PoliteHttpClient, max_description_chars: int) -> None:
        self._http = http
        self._max_chars = max_description_chars

    def fetch(self, slug: str, company: str) -> list[JobPosting]:
        # content=true includes each job's description in the same response (one request).
        data: Any = self._http.get_json(f"{BASE_URL}/{slug}/jobs?content=true")
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise FetchError(f"greenhouse/{slug}: unexpected response shape")
        return [self._to_posting(slug, company, job) for job in data["jobs"] if job.get("id")]

    def _to_posting(self, slug: str, company: str, job: dict[str, Any]) -> JobPosting:
        location = (job.get("location") or {}).get("name")
        return JobPosting(
            source=JobSource.GREENHOUSE,
            company_slug=slug,
            company_name=company,
            external_id=str(job["id"]),
            title=str(job.get("title", "")).strip(),
            location=location,
            is_remote=looks_remote(location),
            url=job.get("absolute_url") or f"https://boards.greenhouse.io/{slug}/jobs/{job['id']}",
            description=html_to_text(job.get("content") or "", self._max_chars),
            posted_at=parse_iso(job.get("first_published") or job.get("updated_at")),
        )
