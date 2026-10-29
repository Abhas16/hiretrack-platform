"""Fill HireTrack with realistic demo data (for screenshots, demos and dashboards).

Tracker data goes through the REAL API (so it exercises auth, validation and the status state
machine). With --with-smart-apply it also inserts sample jobs straight into the database (what
job-scout would store) and scores them in-process (what match-scorer would do), so the Review
queue has matches without calling any job board.

    uv run python scripts/seed-data.py                         # API at http://localhost:8000
    uv run python scripts/seed-data.py --api-url https://hiretrack.example.com --with-smart-apply

Safe to re-run: if the demo user exists it logs in, and existing data is left alone.
Needs DB_* env vars (from .env) only for --with-smart-apply.
"""

import argparse
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

DEMO_EMAIL = "demo@hiretrack.dev"
DEMO_PASSWORD = "demo-password-123"  # noqa: S105 - a public demo account, not a secret
NOW = datetime.now(UTC)

VARIANTS = [
    {"name": "DevOps - Kubernetes", "tags": ["kubernetes", "helm", "aws", "docker", "argo cd"]},
    {"name": "Cloud - Terraform", "tags": ["terraform", "aws", "azure", "ci/cd"]},
    {"name": "SRE - Observability", "tags": ["prometheus", "grafana", "sre", "linux", "python"]},
]

# (company, role, location, source, final status, days ago applied, resume variant index)
APPLICATIONS: list[tuple[str, str, str, str, str, int, int]] = [
    ("Atlassian", "Associate DevOps Engineer", "Bengaluru", "LINKEDIN", "INTERVIEW", 20, 0),
    ("Razorpay", "Site Reliability Engineer I", "Bengaluru", "REFERRAL", "OFFER", 35, 2),
    ("Swiggy", "Platform Engineer", "Bengaluru", "COMPANY_SITE", "APPLIED", 10, 0),
    ("Zerodha", "DevOps Engineer", "Bengaluru", "NAUKRI", "REJECTED", 28, 1),
    ("Freshworks", "Cloud Engineer", "Chennai", "LINKEDIN", "APPLIED", 4, 1),
    ("PhonePe", "Junior SRE", "Pune", "GREENHOUSE", "INTERVIEW", 14, 2),
    ("Postman", "Infrastructure Engineer", "Remote", "LEVER", "APPLIED", 9, 0),
    ("Thoughtworks", "DevOps Consultant", "Pune", "REFERRAL", "WISHLIST", 0, 1),
    ("GitLab", "Support Engineer, Kubernetes", "Remote", "GREENHOUSE", "REJECTED", 40, 0),
    ("Hasura", "Platform Engineer", "Remote", "ASHBY", "WISHLIST", 0, 0),
]
PATH_TO = {
    "WISHLIST": [],
    "APPLIED": [],
    "INTERVIEW": ["INTERVIEW"],
    "OFFER": ["INTERVIEW", "OFFER"],
    "REJECTED": ["REJECTED"],
}

PROFILE = {
    "skills": {
        "kubernetes": 5,
        "docker": 4,
        "terraform": 4,
        "aws": 4,
        "linux": 4,
        "github actions": 3,
        "prometheus": 3,
        "python": 3,
        "bash": 3,
        "helm": 3,
    },
    "target_roles": ["DevOps Engineer", "Platform Engineer", "Site Reliability Engineer", "SRE"],
    "locations": ["Bengaluru", "Pune"],
    "remote_ok": True,
    "years_experience": 1,
}

SAMPLE_JOBS = [
    (
        "Acme Cloud",
        "Junior DevOps Engineer",
        "Remote, India",
        True,
        "Run Kubernetes on AWS (EKS), write Terraform, build GitHub Actions pipelines. "
        "Linux and Bash. 1+ years of experience.",
    ),
    (
        "Nimbus Pay",
        "Platform Engineer",
        "Bengaluru",
        False,
        "Kubernetes, Helm, Argo CD and Prometheus. Python for tooling. Golang a plus. 2+ years.",
    ),
    (
        "Orbit Logistics",
        "Site Reliability Engineer",
        "Pune",
        False,
        "SLOs, Prometheus, Grafana, on-call. Kubernetes and Terraform on AWS. 3-5 years.",
    ),
    (
        "Kite Analytics",
        "Senior Infrastructure Engineer",
        "London",
        False,
        "Terraform, GCP, Kafka and Java. 7+ years leading infrastructure teams.",
    ),
]


class Api:
    def __init__(self, base_url: str) -> None:
        self._http = httpx.Client(base_url=f"{base_url.rstrip('/')}/api/v1", timeout=15)

    def login(self) -> None:
        body = {"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
        response = self._http.post("/auth/register", json={**body, "full_name": "Demo User"})
        if response.status_code not in (201, 409):
            response.raise_for_status()
        token = self.call("POST", "/auth/login", json=body)["access_token"]
        self._http.headers["Authorization"] = f"Bearer {token}"

    def call(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._http.request(method, path, **kwargs)
        if response.is_error:
            sys.exit(f"{method} {path} -> {response.status_code}: {response.text}")
        return response.json() if response.content else None


def seed_tracker(api: Api) -> None:
    if api.call("GET", "/applications", params={"page_size": 1})["total"] > 0:
        print("tracker data already present, skipping")
        return

    variants = {v["name"]: v["id"] for v in api.call("GET", "/resume-variants")}
    ids = [
        variants.get(v["name"]) or api.call("POST", "/resume-variants", json=v)["id"]
        for v in VARIANTS
    ]

    for company, role, location, source, status, days_ago, variant in APPLICATIONS:
        start = "WISHLIST" if status == "WISHLIST" else "APPLIED"
        app = api.call(
            "POST",
            "/applications",
            json={
                "company_name": company,
                "role": role,
                "location": location,
                "source": source,
                "status": start,
                "resume_variant_id": ids[variant],
                "applied_at": None
                if start == "WISHLIST"
                else (NOW - timedelta(days=days_ago)).isoformat(),
            },
        )
        for step in PATH_TO[status]:  # walk the state machine, like a real user would
            api.call("PATCH", f"/applications/{app['id']}/status", json={"status": step})
        if status in ("INTERVIEW", "OFFER"):
            api.call(
                "POST",
                f"/applications/{app['id']}/interviews",
                json={
                    "round_name": "Technical round",
                    "kind": "TECHNICAL",
                    "scheduled_at": (NOW + timedelta(days=2)).isoformat(),
                    "duration_minutes": 60,
                },
            )
        api.call(
            "POST",
            f"/applications/{app['id']}/notes",
            json={"body": f"Found via {source.lower()}."},
        )

    api.call(
        "POST",
        "/reminders",
        json={
            "message": "Update resume with the HireTrack project",
            "due_at": (NOW + timedelta(days=1)).isoformat(),
        },
    )
    print(f"created {len(APPLICATIONS)} applications, {len(VARIANTS)} resume variants")


def seed_smart_apply(api: Api) -> None:
    # Imported here so the tracker-only mode doesn't need the worker packages or DB settings.
    from sqlalchemy import select

    from hiretrack_common.config import DatabaseSettings
    from hiretrack_common.db import create_db_engine, create_session_factory
    from hiretrack_common.db.models import Job
    from hiretrack_common.domain.enums import JobSource
    from hiretrack_common.skills import SkillTaxonomy
    from job_scout.repositories.job_repository import JobRepository
    from job_scout.sources.base import JobPosting
    from match_scorer.repositories.match_repository import MatchRepository
    from match_scorer.services.kit import TemplateKitWriter
    from match_scorer.services.match_service import MatchService

    api.call("PUT", "/match-profile", json=PROFILE)
    engine = create_db_engine(DatabaseSettings())  # type: ignore[call-arg]
    sessions = create_session_factory(engine)
    postings = [
        JobPosting(
            JobSource.GREENHOUSE,
            "demo",
            company,
            f"demo-{i}",
            title,
            location,
            remote,
            f"https://example.com/jobs/demo-{i}",
            text,
            NOW - timedelta(days=i),
        )
        for i, (company, title, location, remote, text) in enumerate(SAMPLE_JOBS)
    ]
    with sessions() as session:
        new_jobs = JobRepository(session).insert_new(postings, NOW)
        session.commit()
        job_ids = list(session.scalars(select(Job.id).where(Job.company_slug == "demo")))

    taxonomy = SkillTaxonomy.load("config/skills.yaml")
    created = 0
    for job_id in job_ids:
        with sessions() as session:
            created += MatchService(
                MatchRepository(session),
                session.commit,
                session.rollback,
                taxonomy,
                TemplateKitWriter(),
                min_score=40,
            ).process(job_id)
    engine.dispose()
    print(f"stored {new_jobs} new sample jobs, created {created} matches")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--with-smart-apply", action="store_true")
    args = parser.parse_args()

    api = Api(args.api_url)
    api.login()
    seed_tracker(api)
    if args.with_smart_apply:
        seed_smart_apply(api)
    print(f"done. Log in as {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
