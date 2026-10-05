"""End-to-end API flows against a real, migrated Postgres."""

import csv
import io
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

API = "/api/v1"
AuthHeaders = dict[str, str]


def create_application(
    client: TestClient, auth: AuthHeaders, company: str, role: str, **extra: object
) -> dict[str, object]:
    response = client.post(
        f"{API}/applications",
        json={"company_name": company, "role": role, **extra},
        headers=auth,
    )
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


def test_readyz_with_a_real_database(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["checks"] == {"database": "ok"}


def test_status_flow_history_and_409(client: TestClient, auth: AuthHeaders) -> None:
    app = create_application(client, auth, "Atlassian", "Associate DevOps Engineer")
    assert app["status"] == "WISHLIST"
    assert app["allowed_transitions"] == ["APPLIED", "REJECTED"]
    url = f"{API}/applications/{app['id']}"

    applied = client.patch(f"{url}/status", json={"status": "APPLIED"}, headers=auth)
    assert applied.status_code == 200
    assert applied.json()["applied_at"] is not None

    assert client.patch(f"{url}/status", json={"status": "INTERVIEW"}, headers=auth).is_success

    backwards = client.patch(f"{url}/status", json={"status": "APPLIED"}, headers=auth)
    assert backwards.status_code == 409
    assert backwards.json()["error"]["code"] == "invalid_status_transition"

    history = client.get(f"{url}/history", headers=auth).json()
    assert [(h["from_status"], h["to_status"]) for h in history] == [
        (None, "WISHLIST"),
        ("WISHLIST", "APPLIED"),
        ("APPLIED", "INTERVIEW"),
    ]


def test_status_cannot_be_changed_through_generic_update(
    client: TestClient, auth: AuthHeaders
) -> None:
    app = create_application(client, auth, "Postman", "DevOps Engineer I")
    response = client.patch(
        f"{API}/applications/{app['id']}", json={"status": "OFFER"}, headers=auth
    )
    assert response.status_code == 422


def test_list_search_filter_sort_and_paginate(client: TestClient, auth: AuthHeaders) -> None:
    create_application(client, auth, "Razorpay", "DevOps Engineer I")
    create_application(client, auth, "Zoho", "Build & Release Engineer", status="APPLIED")
    create_application(client, auth, "Freshworks", "Cloud Engineer", location="Chennai")

    search = client.get(f"{API}/applications", params={"q": "devops"}, headers=auth).json()
    assert [a["company"]["name"] for a in search["items"]] == ["Razorpay"]

    by_location = client.get(f"{API}/applications", params={"q": "chen"}, headers=auth).json()
    assert by_location["total"] == 1

    applied = client.get(f"{API}/applications", params={"status": "APPLIED"}, headers=auth)
    assert [a["company"]["name"] for a in applied.json()["items"]] == ["Zoho"]

    page = client.get(
        f"{API}/applications", params={"sort": "role", "page": 2, "page_size": 2}, headers=auth
    ).json()
    assert page["total"] == 3
    assert [a["role"] for a in page["items"]] == ["DevOps Engineer I"]

    bad_sort = client.get(f"{API}/applications", params={"sort": "password"}, headers=auth)
    assert bad_sort.status_code == 422


def test_board_groups_columns(client: TestClient, auth: AuthHeaders) -> None:
    create_application(client, auth, "TCS", "Azure DevOps Engineer", status="OFFER")
    create_application(client, auth, "Infosys", "Cloud Infrastructure Associate", status="APPLIED")

    columns = client.get(f"{API}/board", headers=auth).json()["columns"]

    assert [(c["status"], c["count"]) for c in columns] == [
        ("WISHLIST", 0),
        ("APPLIED", 1),
        ("INTERVIEW", 0),
        ("OFFER", 1),
        ("REJECTED", 0),
    ]


def test_interviews_notes_and_reminders(client: TestClient, auth: AuthHeaders) -> None:
    app = create_application(client, auth, "EPAM Systems", "Junior DevOps Engineer")
    soon = (datetime.now(UTC) + timedelta(days=1)).isoformat()

    interview = client.post(
        f"{API}/applications/{app['id']}/interviews",
        json={"round_name": "HR screen", "kind": "HR", "scheduled_at": soon},
        headers=auth,
    )
    assert interview.status_code == 201
    assert interview.json()["application"]["company_name"] == "EPAM Systems"

    upcoming = client.get(f"{API}/interviews", params={"upcoming": True}, headers=auth).json()
    assert [i["round_name"] for i in upcoming] == ["HR screen"]

    note = client.post(
        f"{API}/applications/{app['id']}/notes", json={"body": "Referred by Priya"}, headers=auth
    )
    assert note.status_code == 201
    assert client.delete(f"{API}/notes/{note.json()['id']}", headers=auth).status_code == 204

    reminder = client.post(
        f"{API}/reminders",
        json={"application_id": app["id"], "message": "Send thank-you email", "due_at": soon},
        headers=auth,
    ).json()
    done = client.patch(f"{API}/reminders/{reminder['id']}", json={"status": "DONE"}, headers=auth)
    assert done.json()["completed_at"] is not None
    assert client.get(f"{API}/reminders", params={"status": "OPEN"}, headers=auth).json() == []


def test_analytics_endpoints(client: TestClient, auth: AuthHeaders) -> None:
    variant = client.post(
        f"{API}/resume-variants",
        json={"name": "DevOps - Kubernetes", "tags": ["Kubernetes", "kubernetes", "Terraform"]},
        headers=auth,
    ).json()
    assert variant["tags"] == ["Kubernetes", "Terraform"]  # case-insensitive dedupe

    a = create_application(
        client, auth, "Accenture", "Azure Cloud Associate", status="APPLIED",
        source="LINKEDIN", resume_variant_id=variant["id"],
    )  # fmt: skip
    create_application(client, auth, "Maersk", "Platform Engineer I", status="APPLIED")
    create_application(client, auth, "Zoho", "Build & Release Engineer")
    client.patch(f"{API}/applications/{a['id']}/status", json={"status": "INTERVIEW"}, headers=auth)

    summary = client.get(f"{API}/analytics/summary", headers=auth).json()
    assert (summary["total"], summary["sent"], summary["interview_rate"]) == (3, 2, 0.5)

    funnel = client.get(f"{API}/analytics/funnel", headers=auth).json()["stages"]
    assert [s["count"] for s in funnel] == [3, 2, 1, 0]

    weeks = client.get(f"{API}/analytics/per-week", params={"weeks": 4}, headers=auth).json()
    assert weeks["weeks"][-1]["count"] == 2

    by_variant = client.get(f"{API}/analytics/by-resume-variant", headers=auth).json()
    assert by_variant[0]["name"] == "DevOps - Kubernetes"
    assert by_variant[0]["interview_rate"] == 1.0

    ttfi = client.get(f"{API}/analytics/time-to-first-interview", headers=auth).json()
    assert ttfi["sample_size"] == 1


def test_csv_export(client: TestClient, auth: AuthHeaders) -> None:
    create_application(client, auth, "=cmd()", "SRE")

    response = client.get(f"{API}/applications/export.csv", headers=auth)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0][:2] == ["company", "role"]
    assert rows[1][:2] == ["'=cmd()", "SRE"]


def test_company_with_applications_cannot_be_deleted(client: TestClient, auth: AuthHeaders) -> None:
    app = create_application(client, auth, "Thoughtworks", "Associate Infrastructure Consultant")
    company_id = app["company"]["id"]  # type: ignore[index]

    assert client.delete(f"{API}/companies/{company_id}", headers=auth).status_code == 409
    assert client.delete(f"{API}/applications/{app['id']}", headers=auth).status_code == 204
    assert client.delete(f"{API}/companies/{company_id}", headers=auth).status_code == 204


def test_users_cannot_see_each_others_data(
    client: TestClient, register: Callable[[str], AuthHeaders]
) -> None:
    alice = register("alice@example.com")
    bob = register("bob@example.com")
    app = create_application(client, alice, "Groww", "Associate Cloud Engineer")

    assert client.get(f"{API}/applications/{app['id']}", headers=bob).status_code == 404
    assert client.get(f"{API}/applications", headers=bob).json()["total"] == 0
    stolen_status = client.patch(
        f"{API}/applications/{app['id']}/status", json={"status": "APPLIED"}, headers=bob
    )
    assert stolen_status.status_code == 404


def test_auth_errors(client: TestClient, register: Callable[[str], AuthHeaders]) -> None:
    register("dup@example.com")
    duplicate = client.post(
        f"{API}/auth/register",
        json={"email": "DUP@example.com", "password": "another-password", "full_name": "X"},
    )
    assert duplicate.status_code == 409

    bad_login = client.post(
        f"{API}/auth/login", json={"email": "dup@example.com", "password": "nope-nope"}
    )
    assert bad_login.status_code == 401

    bad_token = client.get(f"{API}/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert bad_token.status_code == 401
