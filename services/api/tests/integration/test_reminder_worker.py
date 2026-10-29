"""reminder-worker against a real Postgres: who gets a follow-up, and that reruns are no-ops."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from reminder_worker.repositories.follow_up_repository import FollowUpRepository
from reminder_worker.services.follow_up_service import FollowUpService

pytestmark = pytest.mark.integration

API = "/api/v1"
AuthHeaders = dict[str, str]


def run_worker(engine: Engine) -> int:
    with Session(engine) as session:
        return FollowUpService(FollowUpRepository(session), session.commit, after_days=7).run()


def age(engine: Engine, application_id: str, days: int) -> None:
    """Pretend the application was last touched `days` ago."""
    past = datetime.now(UTC) - timedelta(days=days)
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE applications SET status_changed_at = :t, updated_at = :t, applied_at = :t"
                " WHERE id = :id"
            ),
            {"t": past, "id": application_id},
        )


def create(client: TestClient, auth: AuthHeaders, role: str, status: str) -> str:
    response = client.post(
        f"{API}/applications",
        json={"company_name": "Razorpay", "role": role, "status": status},
        headers=auth,
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def test_follow_ups_for_quiet_applied_applications_only(
    client: TestClient, engine: Engine, auth: AuthHeaders
) -> None:
    stale = create(client, auth, "DevOps Engineer", "APPLIED")
    fresh = create(client, auth, "SRE", "APPLIED")
    wishlist = create(client, auth, "Platform Engineer", "WISHLIST")
    age(engine, stale, 10)
    age(engine, wishlist, 10)
    age(engine, fresh, 2)

    assert run_worker(engine) == 1
    assert run_worker(engine) == 0  # rerun: already reminded

    reminders = client.get(f"{API}/reminders", headers=auth).json()
    assert len(reminders) == 1
    assert reminders[0]["application"]["id"] == stale
    assert reminders[0]["created_by"] == "WORKER"
    assert reminders[0]["kind"] == "FOLLOW_UP"
    assert "applied 10 days ago" in reminders[0]["message"]

    # Dismissing it doesn't make the worker nag again for the same quiet period.
    client.patch(
        f"{API}/reminders/{reminders[0]['id']}", json={"status": "DISMISSED"}, headers=auth
    )
    assert run_worker(engine) == 0
