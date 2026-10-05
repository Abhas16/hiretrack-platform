import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query, status

from hiretrack_api.controllers.deps import CurrentUser, InterviewServiceDep
from hiretrack_api.schemas.interview import InterviewRead, InterviewUpdate

router = APIRouter(tags=["interviews"])


@router.get("/interviews")
def list_interviews(
    user: CurrentUser,
    service: InterviewServiceDep,
    upcoming: Annotated[bool, Query(description="Only pending interviews from now on")] = False,
    scheduled_from: Annotated[datetime | None, Query(alias="from")] = None,
    scheduled_to: Annotated[datetime | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[InterviewRead]:
    interviews = service.list(user.id, upcoming, scheduled_from, scheduled_to, limit)
    return [InterviewRead.model_validate(i) for i in interviews]


@router.get("/interviews/{interview_id}")
def get_interview(
    interview_id: uuid.UUID, user: CurrentUser, service: InterviewServiceDep
) -> InterviewRead:
    return InterviewRead.model_validate(service.get(user.id, interview_id))


@router.patch("/interviews/{interview_id}")
def update_interview(
    interview_id: uuid.UUID,
    body: InterviewUpdate,
    user: CurrentUser,
    service: InterviewServiceDep,
) -> InterviewRead:
    return InterviewRead.model_validate(service.update(user.id, interview_id, body))


@router.delete("/interviews/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(
    interview_id: uuid.UUID, user: CurrentUser, service: InterviewServiceDep
) -> None:
    service.delete(user.id, interview_id)
