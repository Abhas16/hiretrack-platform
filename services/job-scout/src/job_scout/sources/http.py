"""A polite HTTP client: robots.txt, a per-host delay, timeouts, and retries with backoff.

Retry policy:
  429 / 5xx / timeouts / connection errors -> retry, waiting Retry-After if the server sent it,
                                              else base * 2^attempt + jitter (exponential backoff)
  other 4xx (404 = wrong slug)             -> fail at once; retrying can't fix it
"""

import logging
import random
import time
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from job_scout.sources.base import FetchError

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
MAX_RETRY_AFTER_SECONDS = 120.0


class PoliteHttpClient:
    def __init__(
        self,
        client: httpx.Client,
        user_agent: str,
        delay_seconds: float,
        max_retries: int,
        backoff_base_seconds: float,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._client = client
        self._user_agent = user_agent
        self._delay = delay_seconds
        self._max_retries = max_retries
        self._backoff = backoff_base_seconds
        self._sleep = sleep
        self._clock = clock
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser | None] = {}  # None = no rules (allow all)

    def get_json(self, url: str) -> Any:
        if not self._allowed_by_robots(url):
            raise FetchError(f"robots.txt disallows {url}")
        response = self._get_with_retries(url)
        try:
            return response.json()
        except ValueError as exc:
            raise FetchError(f"{url} did not return JSON") from exc

    # ---- retries -----------------------------------------------------------------------
    def _get_with_retries(self, url: str) -> httpx.Response:
        for attempt in range(self._max_retries + 1):
            last_try = attempt == self._max_retries
            self._wait_for_turn(url)
            try:
                response = self._client.get(url, headers={"User-Agent": self._user_agent})
            except httpx.TransportError as exc:  # timeouts, DNS, connection refused/reset
                if last_try:
                    raise FetchError(f"{url}: {type(exc).__name__}") from exc
                self._back_off(url, attempt, None, type(exc).__name__)
                continue

            if response.status_code in RETRYABLE_STATUS and not last_try:
                self._back_off(
                    url, attempt, response.headers.get("Retry-After"), response.status_code
                )
                continue
            if response.is_error:
                raise FetchError(f"{url}: HTTP {response.status_code}")
            return response
        raise FetchError(f"{url}: out of retries")  # unreachable; keeps type checkers happy

    def _back_off(self, url: str, attempt: int, retry_after: str | None, reason: object) -> None:
        wait = _parse_retry_after(retry_after)
        if wait is None:
            # Jitter spreads retries out, so many clients don't all retry at the same instant.
            jitter = random.uniform(0, self._backoff)  # noqa: S311 - not security related
            wait = self._backoff * (2**attempt) + jitter
        logger.warning(
            "retrying request",
            extra={"url": url, "attempt": attempt + 1, "reason": str(reason), "wait_s": wait},
        )
        self._sleep(wait)

    # ---- rate limiting -----------------------------------------------------------------
    def _wait_for_turn(self, url: str) -> None:
        """At most one request per `delay_seconds` to each host."""
        host = urlsplit(url).netloc
        last = self._last_request.get(host)
        if last is not None:
            remaining = self._delay - (self._clock() - last)
            if remaining > 0:
                self._sleep(remaining)
        self._last_request[host] = self._clock()

    # ---- robots.txt --------------------------------------------------------------------
    def _allowed_by_robots(self, url: str) -> bool:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            self._robots[origin] = self._load_robots(origin)
        rules = self._robots[origin]
        return rules is None or rules.can_fetch(self._user_agent, url)

    def _load_robots(self, origin: str) -> RobotFileParser | None:
        """RFC 9309: a 4xx robots.txt means "no rules"; if it can't be fetched at all (5xx,
        network error), assume everything is disallowed, to be safe."""
        robots_url = f"{origin}/robots.txt"
        self._wait_for_turn(robots_url)
        try:
            response = self._client.get(robots_url, headers={"User-Agent": self._user_agent})
        except httpx.TransportError as exc:
            raise FetchError(f"could not read {robots_url}: {type(exc).__name__}") from exc
        if 400 <= response.status_code < 500:
            return None
        if response.is_error:
            raise FetchError(f"could not read {robots_url}: HTTP {response.status_code}")
        parser = RobotFileParser()
        parser.parse(response.text.splitlines())
        return parser


def _parse_retry_after(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return min(max(float(value), 0.0), MAX_RETRY_AFTER_SECONDS)
    except ValueError:
        return None  # HTTP-date form: rare for APIs, fall back to our own backoff
