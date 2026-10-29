"""Smart Apply end to end on a real Postgres: scout stores jobs -> scorer creates matches ->
the review queue API approves/skips them. Uses each service's real repository."""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from hiretrack_common.db.models import Job
from hiretrack_common.domain.enums import JobSource
from hiretrack_common.skills import SkillTaxonomy
from job_scout.repositories.job_repository import JobRepository
from job_scout.sources.base import JobPosting
from match_scorer.repositories.match_repository import MatchRepository
from match_scorer.services.kit import TemplateKitWriter
from match_scorer.services.match_service import MatchService

pytestmark = pytest.mark.integration

API = "/api/v1"
NOW = datetime(2026, 10, 20, 6, 0, tzinfo=UTC)
SKILLS = Path(__file__).resolve().parents[4] / "config" / "skills.yaml"
AuthHeaders = dict[str, str]


def posting(external_id: str, title: str, description: str) -> JobPosting:
    return JobPosting(
        source=JobSource.GREENHOUSE,
        company_slug="acme",
        company_name="Acme Cloud",
        external_id=external_id,
        title=title,
        location="Remote, India",
        is_remote=True,
        url=f"https://boards.greenhouse.io/acme/jobs/{external_id}",
        description=description,
        posted_at=NOW,
    )


GOOD = posting("1", "DevOps Engineer", "Kubernetes on AWS, Terraform, Python. 2+ years.")
OTHER = posting("2", "Platform Engineer", "Kubernetes and Terraform, plus Golang. 5+ years.")


def score_all(engine: Engine) -> int:
    """What the match-scorer does for each queued job ID."""
    taxonomy = SkillTaxonomy.load(SKILLS)
    created = 0
    with Session(engine) as session:
        job_ids = list(session.scalars(select(Job.id)))
    for job_id in job_ids:
        with Session(engine) as session:
            service = MatchService(
                MatchRepository(session),
                session.commit,
                session.rollback,
                taxonomy,
                TemplateKitWriter(),
                min_score=40,
            )
            created += service.process(job_id)
    return created


@pytest.fixture
def smart_user(client: TestClient, register: Callable[[str], AuthHeaders]) -> AuthHeaders:
    auth = register(f"{uuid.uuid4()}@example.com")
    variant = client.post(
        f"{API}/resume-variants",
        json={"name": "DevOps - Kubernetes", "tags": ["kubernetes", "aws", "terraform"]},
        headers=auth,
    )
    assert variant.status_code == 201, variant.text
    profile = client.put(
        f"{API}/match-profile",
        json={
            "skills": {"Kubernetes": 5, "terraform": 4, "aws": 4, "python": 3},
            "target_roles": ["DevOps Engineer", "Platform Engineer"],
            "locations": ["Pune"],
            "years_experience": 2,
        },
        headers=auth,
    )
    assert profile.status_code == 200, profile.text
    assert profile.json()["skills"]["kubernetes"] == 5  # names are lower-cased
    return auth


def test_scout_insert_is_deduplicated_and_outboxed(client: TestClient, engine: Engine) -> None:
    with Session(engine) as session:
        repo = JobRepository(session)
        assert repo.insert_new([GOOD, OTHER, GOOD], NOW) == 2  # duplicate in one batch too
        session.commit()
        assert repo.insert_new([GOOD], NOW) == 0  # a later run: nothing new
        unqueued = repo.list_unqueued(10)
        assert len(unqueued) == 2
        repo.mark_queued(unqueued, NOW)
        session.commit()
        assert repo.list_unqueued(10) == []


def test_review_queue_approve_and_skip(
    client: TestClient, engine: Engine, smart_user: AuthHeaders
) -> None:
    with Session(engine) as session:
        JobRepository(session).insert_new([GOOD, OTHER], NOW)
        session.commit()

    assert score_all(engine) == 2
    assert score_all(engine) == 0  # redelivered messages are no-ops

    queue = client.get(f"{API}/matches", params={"min_score": 0}, headers=smart_user).json()
    assert queue["total"] == 2
    best, second = queue["items"]
    assert best["score"] >= second["score"]
    assert best["job"]["title"] == "DevOps Engineer"
    assert "kubernetes" in best["matched_skills"]
    assert best["suggested_resume_variant"]["name"] == "DevOps - Kubernetes"
    assert len(best["resume_bullets"]) >= 2
    assert any("5+ years" in gap for gap in second["gaps"])

    detail = client.get(f"{API}/matches/{best['id']}", headers=smart_user).json()
    assert "Terraform" in detail["job"]["description"]

    approved = client.post(f"{API}/matches/{best['id']}/approve", headers=smart_user)
    assert approved.status_code == 200, approved.text
    body = approved.json()
    assert body["job_url"] == GOOD.url
    assert body["application"]["status"] == "APPLIED"
    assert body["application"]["source"] == "GREENHOUSE"
    assert body["application"]["company"]["name"] == "Acme Cloud"
    assert body["match"]["status"] == "APPROVED"

    twice = client.post(f"{API}/matches/{best['id']}/approve", headers=smart_user)
    assert twice.status_code == 409

    skipped = client.post(f"{API}/matches/{second['id']}/skip", headers=smart_user)
    assert skipped.json()["status"] == "SKIPPED"

    remaining = client.get(f"{API}/matches", params={"min_score": 0}, headers=smart_user).json()
    assert remaining["total"] == 0  # default filter is status=NEW
    apps = client.get(f"{API}/applications", headers=smart_user).json()
    assert [a["role"] for a in apps["items"]] == ["DevOps Engineer"]


def test_matches_are_private(
    client: TestClient,
    engine: Engine,
    smart_user: AuthHeaders,
    register: Callable[[str], AuthHeaders],
) -> None:
    with Session(engine) as session:
        JobRepository(session).insert_new([GOOD], NOW)
        session.commit()
    score_all(engine)
    [match] = client.get(f"{API}/matches", params={"min_score": 0}, headers=smart_user).json()[
        "items"
    ]

    stranger = register("stranger@example.com")
    assert client.get(f"{API}/matches/{match['id']}", headers=stranger).status_code == 404
    assert client.post(f"{API}/matches/{match['id']}/approve", headers=stranger).status_code == 404


def test_profile_defaults_and_skill_list(client: TestClient, auth: AuthHeaders) -> None:
    profile = client.get(f"{API}/match-profile", headers=auth).json()
    assert profile["exists"] is False
    skills = client.get(f"{API}/match-profile/skills", headers=auth).json()["skills"]
    assert "kubernetes" in skills and "terraform" in skills
