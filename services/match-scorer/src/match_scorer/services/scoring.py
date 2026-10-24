"""Score one job for one profile, 0-100. Pure functions: no I/O, fully unit-tested.

skills      60  your weight of matched skills / (matched + the job's skills you lack)
role        20  best word overlap between the job title and one of your target roles
location    10  remote (if you accept remote) or one of your locations
experience  10  the job's "N+ years" requirement vs your years of experience
"""

import re
from dataclasses import dataclass

from hiretrack_common.skills import SkillTaxonomy
from match_scorer.services.views import JobView, ProfileView

SKILLS_POINTS, ROLE_POINTS, LOCATION_POINTS, EXPERIENCE_POINTS = 60, 20, 10, 10
MAX_SKILL_GAPS = 8

# "5+ years", "3-5 years", "3 to 5 yrs", "2 years". \u2013 is the en dash adverts often use.
# The first number of a range is the minimum.
_YEARS = re.compile(
    r"(?<!\d)(\d{1,2})\s*(?:\+|(?:-|\u2013|to)\s*\d{1,2})?\s*\+?\s*(?:years?|yrs?)(?![a-z])",
    re.IGNORECASE,
)
_WORD = re.compile(r"[a-z0-9+#/]+")
_ROLE_SYNONYMS = {"site reliability": "sre", "dev ops": "devops", "infra ": "infrastructure "}


@dataclass(frozen=True)
class ScoreResult:
    score: int
    matched_skills: list[str]
    gaps: list[str]


def required_years(text: str) -> int | None:
    """The highest "N years" minimum in the advert (the binding requirement), if any.
    Numbers above 20 are ignored ("100 years of history" is not a requirement)."""
    found = [int(m.group(1)) for m in _YEARS.finditer(text)]
    plausible = [n for n in found if 0 < n <= 20]
    return max(plausible) if plausible else None


def score_job(job: JobView, profile: ProfileView, taxonomy: SkillTaxonomy) -> ScoreResult:
    text = f"{job.title}\n{job.description}"
    skill_points, matched, skill_gaps = _skills(text, profile, taxonomy)
    role_points = _role(job.title, profile.target_roles)
    location_points, location_gap = _location(job, profile)
    experience_points, experience_gap = _experience(text, profile.years_experience)

    gaps = skill_gaps + [g for g in (experience_gap, location_gap) if g]
    total = skill_points + role_points + location_points + experience_points
    return ScoreResult(score=max(0, min(100, round(total))), matched_skills=matched, gaps=gaps)


def _skills(
    text: str, profile: ProfileView, taxonomy: SkillTaxonomy
) -> tuple[float, list[str], list[str]]:
    mine = {name.lower(): weight for name, weight in profile.skills.items()}
    matched = [name for name in mine if taxonomy.mentions(name, text)]
    gaps = sorted(taxonomy.extract(text) - set(mine), key=lambda s: (-taxonomy.weight(s), s))

    matched_weight = sum(mine[name] for name in matched)
    gap_weight = sum(taxonomy.weight(name) for name in gaps)
    if matched_weight + gap_weight == 0:
        return 0.0, [], []  # the advert names no skill we know: probably not a tech role
    points = SKILLS_POINTS * matched_weight / (matched_weight + gap_weight)
    matched.sort(key=lambda s: (-mine[s], s))
    return points, matched, gaps[:MAX_SKILL_GAPS]


def _words(text: str) -> set[str]:
    lowered = f"{text.lower()} "
    for phrase, replacement in _ROLE_SYNONYMS.items():
        lowered = lowered.replace(phrase, replacement)
    return set(_WORD.findall(lowered))


def _role(title: str, target_roles: list[str]) -> float:
    if not target_roles:
        return ROLE_POINTS / 2  # no preference given: neutral
    title_words = _words(title)
    best = 0.0
    for role in target_roles:
        role_words = _words(role)
        if role_words:
            best = max(best, len(role_words & title_words) / len(role_words))
    return ROLE_POINTS * best


def _location(job: JobView, profile: ProfileView) -> tuple[float, str | None]:
    if job.is_remote and profile.remote_ok:
        return LOCATION_POINTS, None
    if not profile.locations:
        return LOCATION_POINTS, None  # anywhere is fine
    if not job.location:
        return LOCATION_POINTS / 2, None  # unknown: neither reward nor punish fully
    where = job.location.lower()
    if any(place.lower() in where for place in profile.locations):
        return LOCATION_POINTS, None
    return 0.0, f"Location: {job.location}"


def _experience(text: str, years: int) -> tuple[float, str | None]:
    required = required_years(text)
    if required is None or years >= required:
        return EXPERIENCE_POINTS, None
    gap = f"{required}+ years experience (you have {years})"
    if required - years <= 1:
        return EXPERIENCE_POINTS / 2, gap  # a stretch, still worth applying
    return 0.0, gap
