"""Ashby public Job Postings API (no key): https://developers.ashbyhq.com/docs/public-job-posting-api"""

from typing import Any

from hiretrack_common.domain.enums import JobSource
from job_scout.sources.base import FetchError, JobPosting
from job_scout.sources.http import PoliteHttpClient
from job_scout.sources.text import html_to_text, looks_remote, parse_iso

BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"


class AshbyBoard:
    def __init__(self, http: PoliteHttpClient, max_description_chars: int) -> None:
        self._http = http
        self._max_chars = max_description_chars

    def fetch(self, slug: str, company: str) -> list[JobPosting]:
        data: Any = self._http.get_json(f"{BASE_URL}/{slug}")
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise FetchError(f"ashby/{slug}: unexpected response shape")
        return [
            self._to_posting(slug, company, job)
            for job in data["jobs"]
            if job.get("id") and job.get("isListed", True)  # unlisted = not meant to be public
        ]

    def _to_posting(self, slug: str, company: str, job: dict[str, Any]) -> JobPosting:
        location = job.get("location")
        description = job.get("descriptionPlain") or html_to_text(
            job.get("descriptionHtml") or "", self._max_chars
        )
        return JobPosting(
            source=JobSource.ASHBY,
            company_slug=slug,
            company_name=company,
            external_id=str(job["id"]),
            title=str(job.get("title", "")).strip(),
            location=location,
            is_remote=bool(job.get("isRemote")) or looks_remote(location),
            url=job.get("jobUrl") or f"https://jobs.ashbyhq.com/{slug}/{job['id']}",
            description=description[: self._max_chars],
            posted_at=parse_iso(job.get("publishedAt")),
        )
