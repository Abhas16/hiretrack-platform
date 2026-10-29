"""GitHub Issues REST API, plus a dry-run stand-in for local development.

De-duplication: each issue body carries the alert's fingerprint. Before filing we search open
issues for it. GitHub's search index lags a little, so issues filed by this process in the last
hour are also remembered in memory.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from triage_bot.clients import ClientError

logger = logging.getLogger(__name__)

RECENT_TTL_SECONDS = 3600


@dataclass(frozen=True)
class Issue:
    number: int
    url: str


class IssueTracker(Protocol):
    def find_open(self, fingerprint: str) -> Issue | None: ...
    def create(self, fingerprint: str, title: str, body: str, labels: list[str]) -> Issue: ...
    def comment(self, issue: Issue, body: str) -> None: ...


class GitHubIssues:
    def __init__(self, client: httpx.Client, api_url: str, repo: str, token: str) -> None:
        self._http = client
        self._api = api_url.rstrip("/")
        self._repo = repo
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "hiretrack-triage-bot",
        }
        self._recent: dict[str, tuple[Issue, float]] = {}

    def find_open(self, fingerprint: str) -> Issue | None:
        cached = self._recent.get(fingerprint)
        if cached and time.monotonic() - cached[1] < RECENT_TTL_SECONDS:
            return cached[0]
        query = f'repo:{self._repo} is:issue is:open in:body "{fingerprint}"'
        data = self._request("GET", "/search/issues", params={"q": query, "per_page": 1})
        items = data.get("items", [])
        return Issue(items[0]["number"], items[0]["html_url"]) if items else None

    def create(self, fingerprint: str, title: str, body: str, labels: list[str]) -> Issue:
        data = self._request(
            "POST",
            f"/repos/{self._repo}/issues",
            json={"title": title, "body": body, "labels": labels},
        )
        issue = Issue(data["number"], data["html_url"])
        self._recent[fingerprint] = (issue, time.monotonic())
        return issue

    def comment(self, issue: Issue, body: str) -> None:
        self._request(
            "POST", f"/repos/{self._repo}/issues/{issue.number}/comments", json={"body": body}
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._http.request(
                method, f"{self._api}{path}", headers=self._headers, **kwargs
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ClientError(f"github {method} {path}: {exc}") from exc
        return data


class DryRunIssues:
    """No GITHUB_TOKEN/GITHUB_REPO: log what would be filed (local dev, demos, tests)."""

    def __init__(self) -> None:
        self.created: list[tuple[str, str, list[str]]] = []
        self._open: dict[str, Issue] = {}

    def find_open(self, fingerprint: str) -> Issue | None:
        return self._open.get(fingerprint)

    def create(self, fingerprint: str, title: str, body: str, labels: list[str]) -> Issue:
        issue = Issue(len(self.created) + 1, f"dry-run://issue/{len(self.created) + 1}")
        self.created.append((title, body, labels))
        self._open[fingerprint] = issue
        logger.info("dry run: would open issue", extra={"title": title, "labels": labels})
        return issue

    def comment(self, issue: Issue, body: str) -> None:
        logger.info("dry run: would comment", extra={"issue": issue.number})
