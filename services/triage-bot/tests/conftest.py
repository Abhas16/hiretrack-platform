from datetime import UTC, datetime
from typing import Any

from pydantic import SecretStr

from triage_bot.core.config import TriageSettings
from triage_bot.services.context import LogLine, MetricSeries

NOW = datetime(2026, 10, 20, 6, 15, tzinfo=UTC)
TOKEN = "test-webhook-token-0123456789"
GENERATOR = (
    "http://prometheus:9090/graph?g0.expr="
    "sum(rate(http_requests_total%7Bstatus%3D~%225..%22%7D%5B5m%5D))+%3E+0.05&g0.tab=1"
)


def settings(**overrides: Any) -> TriageSettings:
    values: dict[str, Any] = {
        "webhook_token": SecretStr(TOKEN),
        "app_env": "test",
        "log_format": "console",
        "runbook_base_url": "https://github.com/Abhas16/hiretrack-platform/blob/main/docs/runbooks",
    }
    values.update(overrides)
    return TriageSettings(**values)


def alert_json(
    status: str = "firing",
    fingerprint: str = "a1b2c3d4e5f60718",
    alertname: str = "ApiHighErrorRate",
    **labels: str,
) -> dict[str, Any]:
    return {
        "status": status,
        "labels": {
            "alertname": alertname,
            "severity": "critical",
            "namespace": "hiretrack",
            "app": "api",
            **labels,
        },
        "annotations": {"summary": "API 5xx above 5%", "description": "Error budget burning"},
        "startsAt": "2026-10-20T06:00:00Z",
        "endsAt": "2026-10-20T06:30:00Z" if status == "resolved" else "0001-01-01T00:00:00Z",
        "generatorURL": GENERATOR,
        "fingerprint": fingerprint,
    }


def webhook_json(*alerts: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": "4",
        "status": alerts[0]["status"],
        "receiver": "triage-bot",
        "groupKey": '{}:{alertname="ApiHighErrorRate"}',
        "alerts": list(alerts),
    }


class FakeMetrics:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.queries: list[str] = []

    def range_summary(
        self, query: str, start: datetime, end: datetime, step_seconds: int = 60
    ) -> list[MetricSeries]:
        from triage_bot.clients import ClientError

        self.queries.append(query)
        if self.fail:
            raise ClientError("prometheus: connection refused")
        return [MetricSeries({"route": "/api/v1/applications"}, 0.12, 0.01, 0.2)]

    def instant(self, query: str) -> list[tuple[dict[str, str], float]]:
        self.queries.append(query)
        return [({"pod": "api-7d9f-x2"}, 3.0)]


class FakeLogs:
    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.queries: list[str] = []

    def recent_lines(self, logql: str, start: datetime, end: datetime, limit: int) -> list[LogLine]:
        self.queries.append(logql)
        return [LogLine(NOW, "api-7d9f-x2", line) for line in self.lines][:limit]
