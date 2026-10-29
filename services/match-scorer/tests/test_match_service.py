import uuid

from hiretrack_common.skills import SkillTaxonomy
from match_scorer.services.kit import TemplateKitWriter
from match_scorer.services.match_service import MatchService, NewMatch
from match_scorer.services.views import JobView, ProfileView

from .conftest import make_job, make_profile

STRONG = "Kubernetes on AWS with Terraform, Python and Linux."


class FakeStore:
    def __init__(self, job: JobView | None, profiles: list[ProfileView]) -> None:
        self.job = job
        self.profiles = profiles
        self.matches: dict[tuple[uuid.UUID, uuid.UUID], NewMatch] = {}

    def get_job(self, job_id: uuid.UUID) -> JobView | None:
        return self.job

    def profiles_without_match(self, job_id: uuid.UUID) -> list[ProfileView]:
        return [p for p in self.profiles if (p.user_id, job_id) not in self.matches]

    def insert_match(self, match: NewMatch) -> bool:
        key = (match.user_id, match.job_id)
        if key in self.matches:
            return False
        self.matches[key] = match
        return True


class Calls:
    def __init__(self) -> None:
        self.commits = 0
        self.releases = 0

    def commit(self) -> None:
        self.commits += 1

    def release(self) -> None:
        self.releases += 1


def service(store: FakeStore, taxonomy: SkillTaxonomy, calls: Calls) -> MatchService:
    return MatchService(store, calls.commit, calls.release, taxonomy, TemplateKitWriter(), 40)


def test_stores_matches_above_the_threshold_only(taxonomy: SkillTaxonomy) -> None:
    good = make_profile()
    unrelated = make_profile(skills={"java": 5}, target_roles=["Data Scientist"])
    job = make_job(description=STRONG)
    store, calls = FakeStore(job, [good, unrelated]), Calls()

    assert service(store, taxonomy, calls).process(job.id) == 1

    [match] = store.matches.values()
    assert match.user_id == good.user_id
    assert match.suggested_resume_variant_id is not None
    assert match.kit.cover_note
    assert calls.releases == 1 and calls.commits == 1


def test_redelivery_is_a_no_op(taxonomy: SkillTaxonomy) -> None:
    job = make_job(description=STRONG)
    store, calls = FakeStore(job, [make_profile()]), Calls()

    assert service(store, taxonomy, calls).process(job.id) == 1
    assert service(store, taxonomy, calls).process(job.id) == 0  # same message again
    assert len(store.matches) == 1


def test_missing_job_is_skipped(taxonomy: SkillTaxonomy) -> None:
    store, calls = FakeStore(None, [make_profile()]), Calls()
    assert service(store, taxonomy, calls).process(uuid.uuid4()) == 0
    assert calls.commits == 0
