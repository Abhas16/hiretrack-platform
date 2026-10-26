"""The webhook end to end with fakes for Prometheus/Loki and the dry-run issue tracker."""

from fastapi.testclient import TestClient

from triage_bot.clients.github import DryRunIssues
from triage_bot.main import create_app
from triage_bot.services import cause_rules
from triage_bot.services.gatherer import ContextGatherer
from triage_bot.services.triage_service import TriageService

from .conftest import NOW, TOKEN, FakeLogs, FakeMetrics, alert_json, settings, webhook_json

AUTH = {"Authorization": f"Bearer {TOKEN}"}
DB_ERROR = (
    '{"level": "ERROR", "message": "unhandled error", '
    '"exception": "OperationalError: could not connect"}'
)


def make_client(
    logs: list[str] | None = None, metrics: FakeMetrics | None = None
) -> tuple[TestClient, DryRunIssues, FakeLogs]:
    issues = DryRunIssues()
    fake_logs = FakeLogs(logs or [])
    gatherer = ContextGatherer(metrics or FakeMetrics(), fake_logs, 15, 20, now=lambda: NOW)
    service = TriageService(
        gatherer, cause_rules.analyze, issues, ["incident", "triage-bot"], "https://runbooks"
    )
    return TestClient(create_app(settings(), service)), issues, fake_logs


def test_rejects_calls_without_the_shared_token() -> None:
    client, issues, _ = make_client()
    assert client.post("/webhooks/alertmanager", json=webhook_json(alert_json())).status_code == 401
    wrong = {"Authorization": "Bearer nope"}
    response = client.post("/webhooks/alertmanager", json=webhook_json(alert_json()), headers=wrong)
    assert response.status_code == 401
    assert issues.created == []


def test_firing_alert_opens_one_issue_with_context() -> None:
    client, issues, fake_logs = make_client(logs=[DB_ERROR, "```@here```"])

    response = client.post("/webhooks/alertmanager", json=webhook_json(alert_json()), headers=AUTH)

    assert response.status_code == 200
    assert response.json()["results"][0]["action"] == "created"
    [(title, body, labels)] = issues.created
    assert title == "[CRITICAL] ApiHighErrorRate: API 5xx above 5%"
    assert labels == ["incident", "triage-bot", "severity:critical"]
    assert "database" in body.lower()  # the database rule won: logs show OperationalError
    assert "OperationalError" in body
    assert "| `api-7d9f-x2` | 3 |" in body  # affected pods
    assert 'sum(rate(http_requests_total{status=~"5.."}[5m])) > 0.05' in body
    assert "https://runbooks/ApiHighErrorRate.md" in body
    assert "a1b2c3d4e5f60718" in body  # fingerprint for de-duplication
    assert body.count("```") == 2  # a fence inside a log line can't break out of the block
    assert fake_logs.queries == [
        '{app="api",namespace="hiretrack"} '
        '|~ "(?i)(error|warn|critical|exception|traceback|fault injected)"'
    ]


def test_repeat_notifications_do_not_open_duplicates() -> None:
    client, issues, _ = make_client()
    for _ in range(3):
        client.post("/webhooks/alertmanager", json=webhook_json(alert_json()), headers=AUTH)
    assert len(issues.created) == 1


def test_resolved_alert_comments_on_its_issue() -> None:
    client, _, _ = make_client()
    client.post("/webhooks/alertmanager", json=webhook_json(alert_json()), headers=AUTH)

    resolved = webhook_json(alert_json(status="resolved"))
    response = client.post("/webhooks/alertmanager", json=resolved, headers=AUTH)
    assert response.json()["results"][0]["action"] == "resolved_comment"

    unknown = webhook_json(alert_json(status="resolved", fingerprint="ffff"))
    response = client.post("/webhooks/alertmanager", json=unknown, headers=AUTH)
    assert response.json()["results"][0]["action"] == "ignored"


def test_prometheus_outage_still_files_the_issue() -> None:
    client, issues, _ = make_client(metrics=FakeMetrics(fail=True))
    response = client.post("/webhooks/alertmanager", json=webhook_json(alert_json()), headers=AUTH)
    assert response.status_code == 200
    body = issues.created[0][1]
    assert "Missing context" in body
    assert "prometheus unavailable" in body


def test_rejects_malformed_payloads() -> None:
    client, _, _ = make_client()
    bad = webhook_json(alert_json(fingerprint="not-hex!"))
    assert client.post("/webhooks/alertmanager", json=bad, headers=AUTH).status_code == 422


def test_health() -> None:
    client, _, _ = make_client()
    assert client.get("/healthz").json() == {"status": "ok"}
    assert "triage_alerts_total" in client.get("/metrics").text
