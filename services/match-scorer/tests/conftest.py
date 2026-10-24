import uuid
from pathlib import Path

import pytest

from hiretrack_common.skills import SkillTaxonomy
from match_scorer.services.views import JobView, ProfileView, VariantView

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def taxonomy() -> SkillTaxonomy:
    """The real config/skills.yaml, so a broken taxonomy file fails the tests."""
    return SkillTaxonomy.load(REPO_ROOT / "config" / "skills.yaml")


def make_job(
    title: str = "DevOps Engineer",
    description: str = "",
    location: str | None = "Pune",
    is_remote: bool = False,
) -> JobView:
    return JobView(
        id=uuid.uuid4(),
        company_name="Acme",
        title=title,
        location=location,
        is_remote=is_remote,
        description=description,
    )


def make_profile(**overrides: object) -> ProfileView:
    values: dict[str, object] = {
        "user_id": uuid.uuid4(),
        "skills": {"kubernetes": 5, "terraform": 4, "aws": 4, "python": 3, "linux": 3},
        "target_roles": ["DevOps Engineer", "Platform Engineer", "SRE"],
        "locations": ["Pune", "Bengaluru"],
        "remote_ok": True,
        "years_experience": 2,
        "variants": [
            VariantView(uuid.uuid4(), "DevOps - Kubernetes", ["kubernetes", "helm", "aws"]),
            VariantView(uuid.uuid4(), "Cloud - Terraform", ["terraform", "aws"]),
        ],
    }
    values.update(overrides)
    return ProfileView(**values)  # type: ignore[arg-type]
