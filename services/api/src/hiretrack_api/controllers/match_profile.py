"""The user's Smart Apply profile: the skills, roles and locations the scorer matches against."""

from fastapi import APIRouter, Request

from hiretrack_api.controllers.deps import CurrentUser, MatchServiceDep
from hiretrack_api.models import MatchProfile
from hiretrack_api.schemas.match import MatchProfileRead, MatchProfileUpdate, SkillListRead

router = APIRouter(prefix="/match-profile", tags=["review queue"])


def _read(profile: MatchProfile | None) -> MatchProfileRead:
    if profile is None:
        return MatchProfileRead(
            exists=False,
            is_active=False,
            skills={},
            target_roles=[],
            locations=[],
            remote_ok=True,
            years_experience=0,
            updated_at=None,
        )
    return MatchProfileRead(
        exists=True,
        is_active=profile.is_active,
        skills=profile.skills,
        target_roles=profile.target_roles,
        locations=profile.locations,
        remote_ok=profile.remote_ok,
        years_experience=profile.years_experience,
        updated_at=profile.updated_at,
    )


@router.get("")
def get_profile(user: CurrentUser, service: MatchServiceDep) -> MatchProfileRead:
    return _read(service.get_profile(user.id))


@router.put("")
def save_profile(
    body: MatchProfileUpdate, user: CurrentUser, service: MatchServiceDep
) -> MatchProfileRead:
    return _read(service.save_profile(user.id, body))


@router.get("/skills")
def list_skills(request: Request, _: CurrentUser) -> SkillListRead:
    """Skill names from config/skills.yaml, for the profile form's picker."""
    return SkillListRead(skills=request.app.state.skill_names)
