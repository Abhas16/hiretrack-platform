"""The polite client: retries with backoff, Retry-After, no retry on 404, robots.txt, rate limit."""

from collections.abc import Callable

import httpx
import pytest

from job_scout.sources import FetchError, PoliteHttpClient

from .conftest import Router, SleepRecorder

API = "https://api.example.com/jobs"


def sequence(*responses: httpx.Response) -> Router:
    """robots.txt -> 404 (no rules); API calls get the given responses in order."""
    queue = list(responses)
    calls: list[str] = []

    def router(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        calls.append(request.headers["User-Agent"])
        return queue.pop(0)

    router.calls = calls  # type: ignore[attr-defined]
    return router


MakeHttp = Callable[..., PoliteHttpClient]


def test_retries_5xx_with_exponential_backoff(make_http: MakeHttp, sleeps: SleepRecorder) -> None:
    router = sequence(httpx.Response(503), httpx.Response(502), httpx.Response(200, json=[1]))
    assert make_http(router).get_json(API) == [1]
    backoffs = [s for s in sleeps.calls if s > 0]
    assert len(backoffs) == 2
    assert 1.0 <= backoffs[0] < 2.0  # 1 * 2^0 + jitter(0..1)
    assert 2.0 <= backoffs[1] < 3.0  # 1 * 2^1 + jitter(0..1)


def test_honours_retry_after(make_http: MakeHttp, sleeps: SleepRecorder) -> None:
    router = sequence(
        httpx.Response(429, headers={"Retry-After": "7"}), httpx.Response(200, json={})
    )
    make_http(router).get_json(API)
    assert 7.0 in sleeps.calls


def test_gives_up_after_max_retries(make_http: MakeHttp) -> None:
    router = sequence(*[httpx.Response(500)] * 3)
    with pytest.raises(FetchError, match="HTTP 500"):
        make_http(router, retries=2).get_json(API)


def test_does_not_retry_404(make_http: MakeHttp) -> None:
    router = sequence(httpx.Response(404))
    with pytest.raises(FetchError, match="HTTP 404"):
        make_http(router).get_json(API)
    assert len(router.calls) == 1  # type: ignore[attr-defined]


def test_sends_honest_user_agent(make_http: MakeHttp) -> None:
    router = sequence(httpx.Response(200, json={}))
    make_http(router).get_json(API)
    assert router.calls == ["HireTrackScout-test"]  # type: ignore[attr-defined]


def test_respects_robots_disallow(make_http: MakeHttp) -> None:
    def router(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /jobs\n")
        raise AssertionError("the API must not be called")

    with pytest.raises(FetchError, match="robots.txt disallows"):
        make_http(router).get_json(API)


def test_unreachable_robots_means_disallow(make_http: MakeHttp) -> None:
    def router(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    with pytest.raises(FetchError, match="robots.txt"):
        make_http(router).get_json(API)


def test_waits_between_requests_to_the_same_host(
    make_http: MakeHttp, sleeps: SleepRecorder
) -> None:
    router = sequence(httpx.Response(200, json={}), httpx.Response(200, json={}))
    http = make_http(router, delay=1.5)
    http.get_json(API)
    http.get_json(API)
    # frozen clock -> each request after the first waits the full delay (robots, api, api)
    assert sleeps.calls == [1.5, 1.5]
