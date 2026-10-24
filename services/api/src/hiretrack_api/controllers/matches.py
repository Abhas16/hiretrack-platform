"""Smart Apply review queue: list scored matches, approve (I'm applying) or skip."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from hiretrack_api.controllers.deps import CurrentUser, MatchServiceDep
from hiretrack_api.schemas.application import ApplicationRead
from hiretrack_api.schemas.common import Page
from hiretrack_api.schemas.match import ApproveResponse, MatchDetail, MatchRead
from hiretrack_common.domain.enums import MatchStatus

router = APIRouter(prefix="/matches", tags=["review queue"])


@router.get("")
def list_matches(
    user: CurrentUser,
    service: MatchServiceDep,
    status_: Annotated[MatchStatus | None, Query(alias="status")] = MatchStatus.NEW,
    min_score: Annotated[int, Query(ge=0, le=100)] = 60,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[MatchRead]:
    items, total = service.search(user.id, status_, min_score, page, page_size)
    return Page[MatchRead](
        items=[MatchRead.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{match_id}")
def get_match(match_id: uuid.UUID, user: CurrentUser, service: MatchServiceDep) -> MatchDetail:
    return MatchDetail.model_validate(service.get(user.id, match_id))


@router.post("/{match_id}/approve")
def approve_match(
    match_id: uuid.UUID, user: CurrentUser, service: MatchServiceDep
) -> ApproveResponse:
    match, application = service.approve(user.id, match_id)
    return ApproveResponse(
        match=MatchRead.model_validate(match),
        application=ApplicationRead.model_validate(application),
        job_url=match.job.url,
    )


@router.post("/{match_id}/skip")
def skip_match(match_id: uuid.UUID, user: CurrentUser, service: MatchServiceDep) -> MatchRead:
    return MatchRead.model_validate(service.skip(user.id, match_id))
