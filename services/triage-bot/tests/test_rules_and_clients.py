"""Cause rules, query building, and the HTTP clients against recorded API shapes."""

import json
from typing import Any

import httpx
import pytest

from triage_bot.clients import ClientError
from triage_bot.clients.github import GitHubIssues
from triage_bot.clients.loki import LokiClient
from triage_bot.clients.prometheus import PrometheusClient
from triage_bot.clients.promql import selector
from triage_bot.schemas.alertmanager import Alert
from triage_bot.services.cause_rules import analyze
from triage_bot.services.context import AlertContext, LogLine, PodRestarts
from triage_bot.services.gatherer import alert_expression

from .conftest import GENERATOR, NOW, alert_json


def make_alert(alertname: str = "ApiHighErrorRate") -> Alert:
    return Alert.model_validate(alert_json(alertname=alertname))


def ctx(lines: list[str] = (), restarts: int = 0) -> AlertContext:  # type: ignore[assignment]
    context = AlertContext(window_start=NOW, window_end=NOW)
    context.logs = [LogLine(NOW, "api-1", line) for line in lines]
    if restarts:
        context.restarts = [PodRestarts("api-1", restarts)]
    return context


@pytest.mark.parametrize(
    ("alertname", "lines", "restarts", "rule"),
    [
        ("ApiHighErrorRate", ['"message": "fault injected"'], 0, "chaos-experiment"),
        ("ApiHighErrorRate", ["psycopg.OperationalError: connection refused"], 0, "database"),
        ("PodMemoryHigh", [], 0, "out-of-memory"),
        ("Anything", [], 2, "crash-loop"),
        ("ScorerDLQNotEmpty", [], 0, "queue"),
        ("ScoutRunsStale", [], 0, "scout"),
        ("ApiLatencyP95High", [], 0, "latency"),
        ("ApiErrorBudgetBurn", [], 0, "error-rate"),
        ("DiskFull", [], 0, "unknown"),
    ],
)
def test_first_matching_rule_wins(
    alertname: str, lines: list[str], restarts: int, rule: str
) -> None:
    assert analyze(make_alert(alertname), ctx(lines, restarts)).rule == rule


def test_alert_expression_comes_from_the_generator_url() -> None:
    assert alert_expression(GENERATOR) == 'sum(rate(http_requests_total{status=~"5.."}[5m])) > 0.05'
    assert alert_expression("") is None


def test_selector_escapes_label_values() -> None:
    assert selector({"app": 'x"} or vector(1) #'}) == '{app="x\\"} or vector(1) #"}'


def mock(handler: Any) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_prometheus_summarises_range_series() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/query_range"
        return httpx.Response(
            200,
            json={
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {"metric": {"route": "/x"}, "values": [[1, "0.5"], [2, "NaN"], [3, "0.1"]]}
                    ],
                },
            },
        )

    [series] = PrometheusClient(mock(handler), "http://prom").range_summary("up", NOW, NOW)
    assert (series.last, series.minimum, series.maximum) == (0.1, 0.1, 0.5)


def test_prometheus_errors_become_client_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "error", "error": "parse error"})

    with pytest.raises(ClientError, match="parse error"):
        PrometheusClient(mock(handler), "http://prom").instant("up{")


def test_loki_merges_streams_newest_first() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["direction"] == "backward"
        return httpx.Response(
            200,
            json={
                "data": {
                    "resultType": "streams",
                    "result": [
                        {"stream": {"pod": "a"}, "values": [["1760940000000000000", "old"]]},
                        {"stream": {"pod": "b"}, "values": [["1760940060000000000", "new"]]},
                    ],
                }
            },
        )

    lines = LokiClient(mock(handler), "http://loki").recent_lines("{}", NOW, NOW, 10)
    assert [(entry.pod, entry.line) for entry in lines] == [("b", "new"), ("a", "old")]


def test_github_searches_by_fingerprint_and_creates() -> None:
    calls: list[tuple[str, str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        calls.append((request.method, request.url.path, body))
        assert request.headers["Authorization"] == "Bearer ghp-test"
        if request.url.path == "/search/issues":
            assert '"abc123"' in request.url.params["q"]
            return httpx.Response(200, json={"items": []})
        return httpx.Response(
            201, json={"number": 7, "html_url": "https://github.com/o/r/issues/7"}
        )

    github = GitHubIssues(mock(handler), "https://api.github.com", "o/r", "ghp-test")
    assert github.find_open("abc123") is None
    issue = github.create("abc123", "title", "body", ["incident"])
    assert issue.number == 7
    assert github.find_open("abc123") == issue  # remembered: no second search needed
    assert [c[1] for c in calls] == ["/search/issues", "/repos/o/r/issues"]
    assert calls[1][2] == {"title": "title", "body": "body", "labels": ["incident"]}
