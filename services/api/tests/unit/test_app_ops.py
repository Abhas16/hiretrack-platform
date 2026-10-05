"""App-level behaviour that needs no database: ops endpoints, middleware, auth errors."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from hiretrack_api.core.config import ApiSettings
from hiretrack_api.main import create_app


@pytest.fixture
def client(api_settings: ApiSettings) -> Iterator[TestClient]:
    with TestClient(create_app(api_settings)) as test_client:
        yield test_client


@pytest.fixture
def chaos_client(api_settings: ApiSettings) -> Iterator[TestClient]:
    settings = api_settings.model_copy(update={"fault_injection_rate": 1.0})
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_healthz_never_touches_the_database(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_reports_failed_database(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "checks": {"database": "failed"}}


def test_request_id_is_echoed_when_safe_and_replaced_when_not(client: TestClient) -> None:
    assert client.get("/healthz", headers={"X-Request-ID": "abc-123"}).headers["X-Request-ID"] == (
        "abc-123"
    )
    unsafe = client.get("/healthz", headers={"X-Request-ID": "bad id\nwith newline"})
    assert unsafe.headers["X-Request-ID"] != "bad id\nwith newline"
    assert len(unsafe.headers["X-Request-ID"]) == 32


def test_protected_endpoint_without_token_is_401(client: TestClient) -> None:
    response = client.get("/api/v1/applications")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "unauthorized"


def test_fault_injection_fails_api_calls_but_not_probes(chaos_client: TestClient) -> None:
    api = chaos_client.get("/api/v1/applications")
    assert api.status_code == 500
    assert api.json()["error"]["code"] == "injected_fault"
    assert chaos_client.get("/healthz").status_code == 200


def test_metrics_use_route_templates_and_count_injected_faults(
    chaos_client: TestClient,
) -> None:
    chaos_client.get("/api/v1/applications/3fa85f64-5717-4562-b3fc-2c963f66afa6")
    body = chaos_client.get("/metrics").text

    assert 'route="/api/v1/applications/{application_id}"' in body
    assert "3fa85f64" not in body  # raw IDs would explode metric cardinality
    assert "fault_injections_total" in body
    assert "http_request_duration_seconds_bucket" in body


def test_settings_reject_short_jwt_secret(api_settings: ApiSettings) -> None:
    with pytest.raises(ValueError, match="at least 32"):
        ApiSettings(db_password="x", jwt_secret="too-short")  # type: ignore[arg-type]
