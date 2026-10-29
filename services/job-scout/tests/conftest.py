"""Serve recorded board responses through httpx.MockTransport: tests never touch the network."""

import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from job_scout.sources.http import PoliteHttpClient

FIXTURES = Path(__file__).parent / "fixtures"

type Router = Callable[[httpx.Request], httpx.Response]


def load_fixture(name: str) -> object:
    return json.loads((FIXTURES / name).read_text("utf-8"))


class SleepRecorder:
    """Stands in for time.sleep, so backoff and rate-limit waits are instant but checkable."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


@pytest.fixture
def sleeps() -> SleepRecorder:
    return SleepRecorder()


@pytest.fixture
def make_http(sleeps: SleepRecorder) -> Callable[[Router], PoliteHttpClient]:
    def _make(router: Router, delay: float = 0.0, retries: int = 2) -> PoliteHttpClient:
        client = httpx.Client(transport=httpx.MockTransport(router))
        return PoliteHttpClient(
            client,
            user_agent="HireTrackScout-test",
            delay_seconds=delay,
            max_retries=retries,
            backoff_base_seconds=1.0,
            sleep=sleeps,
            clock=lambda: 0.0,  # frozen clock: every request looks "immediately after" the last
        )

    return _make


def boards_router(request: httpx.Request) -> httpx.Response:
    """Robots.txt allows everything (404 = no rules); each board API returns its fixture."""
    url = str(request.url)
    if url.endswith("/robots.txt"):
        return httpx.Response(404)
    if "greenhouse" in url:
        return httpx.Response(200, json=load_fixture("greenhouse_jobs.json"))
    if "lever" in url:
        return httpx.Response(200, json=load_fixture("lever_postings.json"))
    if "ashby" in url:
        return httpx.Response(200, json=load_fixture("ashby_job_board.json"))
    return httpx.Response(404)
