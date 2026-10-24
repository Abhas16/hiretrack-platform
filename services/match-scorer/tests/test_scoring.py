import pytest

from hiretrack_common.skills import SkillTaxonomy
from match_scorer.services.resume_picker import pick_variant
from match_scorer.services.scoring import required_years, score_job

from .conftest import make_job, make_profile

STRONG = (
    "Run Kubernetes (EKS) on AWS. Infrastructure as code with Terraform. "
    "Python scripting, Linux. 2+ years of experience."
)


@pytest.mark.parametrize(
    ("text", "years"),
    [
        ("5+ years of experience", 5),
        ("3-5 years in DevOps", 3),
        ("3 \u2013 5 yrs", 3),
        ("3 to 5 years", 3),
        ("2 years with Linux and 4+ years overall", 4),  # the binding (highest) minimum
        ("no requirement", None),
        ("a company with 150 years of history", None),  # not plausible as a requirement
    ],
)
def test_required_years(text: str, years: int | None) -> None:
    assert required_years(text) == years


def test_strong_match_scores_high(taxonomy: SkillTaxonomy) -> None:
    result = score_job(make_job(description=STRONG), make_profile(), taxonomy)
    assert result.score == 100
    assert result.matched_skills[:2] == ["kubernetes", "aws"]  # sorted by your weight
    assert result.gaps == []


def test_skill_gaps_lower_the_score_and_are_listed(taxonomy: SkillTaxonomy) -> None:
    job = make_job(description=f"{STRONG} Also Golang, Kafka and Jenkins.")
    result = score_job(job, make_profile(), taxonomy)
    assert 70 <= result.score < 100
    assert set(result.gaps) == {"go", "kafka", "jenkins"}
    assert result.gaps[0] in {"go", "jenkins"}  # heavier gaps first


def test_years_gap_is_detected(taxonomy: SkillTaxonomy) -> None:
    job = make_job(description="Kubernetes and Terraform. 5+ years of experience required.")
    result = score_job(job, make_profile(years_experience=2), taxonomy)
    assert "5+ years experience (you have 2)" in result.gaps


def test_location_mismatch_unless_remote(taxonomy: SkillTaxonomy) -> None:
    onsite = score_job(make_job(description=STRONG, location="London"), make_profile(), taxonomy)
    remote = score_job(
        make_job(description=STRONG, location="London", is_remote=True), make_profile(), taxonomy
    )
    assert "Location: London" in onsite.gaps
    assert remote.score - onsite.score == 10


def test_role_synonyms(taxonomy: SkillTaxonomy) -> None:
    sre = score_job(
        make_job(title="Site Reliability Engineer", description=STRONG), make_profile(), taxonomy
    )
    sales = score_job(
        make_job(title="Account Executive", description=STRONG), make_profile(), taxonomy
    )
    assert sre.score > sales.score


def test_non_tech_advert_scores_low(taxonomy: SkillTaxonomy) -> None:
    job = make_job(title="Account Executive", description="Sell to enterprise customers.")
    assert score_job(job, make_profile(), taxonomy).score < 40


def test_alias_whole_word_matching(taxonomy: SkillTaxonomy) -> None:
    assert taxonomy.extract("We use k8s and CI/CD daily") == {"kubernetes", "ci/cd"}
    assert "git" not in taxonomy.extract("legitimate digital work")  # no substring matches


def test_pick_variant_by_tag_overlap() -> None:
    profile = make_profile()
    assert pick_variant(profile.variants, ["terraform", "aws"]).name == "Cloud - Terraform"  # type: ignore[union-attr]
    assert pick_variant(profile.variants, ["kubernetes", "helm"]).name == "DevOps - Kubernetes"  # type: ignore[union-attr]
    assert pick_variant(profile.variants, ["python"]) is None
