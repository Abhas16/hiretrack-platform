"""Practice interview end to end, with the default rule-based interviewer (no LLM, no cost)."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

API = "/api/v1/practice"
AuthHeaders = dict[str, str]


def test_meta_lists_provider_and_topics(client: TestClient, auth: AuthHeaders) -> None:
    meta = client.get(f"{API}/meta", headers=auth).json()
    assert meta["provider"] == "rule_based"
    assert {"id": "kubernetes", "label": "Kubernetes"} in meta["topics"]


def test_full_mock_interview(client: TestClient, auth: AuthHeaders) -> None:
    started = client.post(
        f"{API}/sessions",
        json={
            "role": "Junior DevOps Engineer",
            "topics": ["kubernetes", "docker"],
            "question_count": 3,
        },
        headers=auth,
    )
    assert started.status_code == 201, started.text
    session = started.json()
    assert [t["topic"] for t in session["turns"]] == ["kubernetes", "docker", "kubernetes"]
    assert all(t["key_points"] == [] for t in session["turns"])  # no spoilers yet

    for _ in range(3):
        response = client.post(
            f"{API}/sessions/{session['id']}/answers",
            json={
                "answer": "A container restarts when the liveness probe fails; readiness "
                "removes the pod from the Service endpoints so it gets no traffic."
            },
            headers=auth,
        )
        assert response.status_code == 200, response.text
        session = response.json()

    assert session["status"] == "COMPLETED"
    assert session["answered_count"] == 3
    assert session["average_score"] is not None
    first = session["turns"][0]
    assert 0 <= first["score"] <= 10
    assert first["key_points"]  # revealed after answering
    assert first["evaluated_by"] == "rule_based"

    finished = client.post(
        f"{API}/sessions/{session['id']}/answers", json={"answer": "x"}, headers=auth
    )
    assert finished.status_code == 409

    history = client.get(f"{API}/sessions", headers=auth).json()
    assert history[0]["id"] == session["id"]
    assert "turns" not in history[0]


def test_session_for_an_application_uses_its_role(client: TestClient, auth: AuthHeaders) -> None:
    app = client.post(
        "/api/v1/applications",
        json={
            "company_name": "Hasura",
            "role": "Site Reliability Engineer I",
            "status": "INTERVIEW",
        },
        headers=auth,
    ).json()

    session = client.post(
        f"{API}/sessions", json={"application_id": app["id"]}, headers=auth
    ).json()

    assert session["role"] == "Site Reliability Engineer I"
    assert session["topics"][0] == "observability"
    assert session["application_id"] == app["id"]


def test_validation_and_ownership(client: TestClient, register) -> None:  # type: ignore[no-untyped-def]
    alice, bob = register("alice@example.com"), register("bob@example.com")

    assert client.post(f"{API}/sessions", json={}, headers=alice).status_code == 422
    too_many = client.post(
        f"{API}/sessions", json={"role": "SRE", "question_count": 20}, headers=alice
    )
    assert too_many.status_code == 422

    session = client.post(f"{API}/sessions", json={"role": "SRE"}, headers=alice).json()
    assert client.get(f"{API}/sessions/{session['id']}", headers=bob).status_code == 404
    assert client.delete(f"{API}/sessions/{session['id']}", headers=alice).status_code == 204
