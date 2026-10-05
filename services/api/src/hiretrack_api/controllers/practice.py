import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from hiretrack_api.controllers.deps import CurrentUser, PracticeServiceDep
from hiretrack_api.schemas.practice import (
    PracticeAnswerCreate,
    PracticeMetaRead,
    PracticeSessionCreate,
    PracticeSessionRead,
    PracticeSessionSummary,
    PracticeTopicRead,
)

router = APIRouter(prefix="/practice", tags=["practice interview"])


@router.get("/meta")
def practice_meta(_user: CurrentUser, service: PracticeServiceDep) -> PracticeMetaRead:
    return PracticeMetaRead(
        provider=service.provider,
        topics=[PracticeTopicRead(id=key, label=label) for key, label in service.topics().items()],
    )


@router.get("/sessions")
def list_sessions(
    user: CurrentUser,
    service: PracticeServiceDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[PracticeSessionSummary]:
    return [PracticeSessionSummary.model_validate(s) for s in service.list(user.id, limit)]


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def start_session(
    body: PracticeSessionCreate, user: CurrentUser, service: PracticeServiceDep
) -> PracticeSessionRead:
    return PracticeSessionRead.model_validate(service.create(user.id, body))


@router.get("/sessions/{session_id}")
def get_session(
    session_id: uuid.UUID, user: CurrentUser, service: PracticeServiceDep
) -> PracticeSessionRead:
    return PracticeSessionRead.model_validate(service.get(user.id, session_id))


@router.post(
    "/sessions/{session_id}/answers",
    responses={409: {"description": "Session finished, or question already answered"}},
)
def answer_question(
    session_id: uuid.UUID,
    body: PracticeAnswerCreate,
    user: CurrentUser,
    service: PracticeServiceDep,
) -> PracticeSessionRead:
    return PracticeSessionRead.model_validate(service.answer(user.id, session_id, body.answer))


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: uuid.UUID, user: CurrentUser, service: PracticeServiceDep) -> None:
    service.delete(user.id, session_id)
