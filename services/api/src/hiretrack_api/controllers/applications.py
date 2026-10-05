import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from hiretrack_api.controllers.deps import (
    ApplicationServiceDep,
    CurrentUser,
    InterviewServiceDep,
    NoteServiceDep,
)
from hiretrack_api.repositories.application_repository import ApplicationFilters
from hiretrack_api.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    BoardColumn,
    BoardRead,
    StatusChangeRequest,
    StatusHistoryRead,
)
from hiretrack_api.schemas.common import Page
from hiretrack_api.schemas.interview import InterviewCreate, InterviewRead
from hiretrack_api.schemas.note import NoteCreate, NoteRead
from hiretrack_common.domain.enums import ApplicationSource, ApplicationStatus

router = APIRouter(tags=["applications"])

SORT_PATTERN = r"^-?(updated_at|created_at|applied_at|role|status)$"


def _filters(
    status_: list[ApplicationStatus] | None,
    company_id: uuid.UUID | None,
    source: ApplicationSource | None,
    resume_variant_id: uuid.UUID | None,
    q: str | None,
    applied_from: datetime | None,
    applied_to: datetime | None,
) -> ApplicationFilters:
    return ApplicationFilters(
        statuses=tuple(status_ or ()),
        company_id=company_id,
        source=source,
        resume_variant_id=resume_variant_id,
        q=q.strip() if q and q.strip() else None,
        applied_from=applied_from,
        applied_to=applied_to,
    )


# Query parameters shared by the list and the CSV export.
StatusQ = Annotated[list[ApplicationStatus] | None, Query(alias="status")]
CompanyQ = Annotated[uuid.UUID | None, Query()]
SourceQ = Annotated[ApplicationSource | None, Query()]
VariantQ = Annotated[uuid.UUID | None, Query()]
SearchQ = Annotated[str | None, Query(max_length=100, description="Role, company or location")]
DateQ = Annotated[datetime | None, Query()]


@router.get("/applications")
def list_applications(
    user: CurrentUser,
    service: ApplicationServiceDep,
    status_: StatusQ = None,
    company_id: CompanyQ = None,
    source: SourceQ = None,
    resume_variant_id: VariantQ = None,
    q: SearchQ = None,
    applied_from: DateQ = None,
    applied_to: DateQ = None,
    sort: Annotated[str, Query(pattern=SORT_PATTERN)] = "-updated_at",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> Page[ApplicationRead]:
    filters = _filters(status_, company_id, source, resume_variant_id, q, applied_from, applied_to)
    items, total = service.search(user.id, filters, sort, page, page_size)
    return Page[ApplicationRead](
        items=[ApplicationRead.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# Declared before /applications/{application_id} so "export.csv" isn't parsed as an ID.
@router.get("/applications/export.csv", response_class=Response)
def export_applications(
    user: CurrentUser,
    service: ApplicationServiceDep,
    status_: StatusQ = None,
    company_id: CompanyQ = None,
    source: SourceQ = None,
    resume_variant_id: VariantQ = None,
    q: SearchQ = None,
    applied_from: DateQ = None,
    applied_to: DateQ = None,
) -> Response:
    filters = _filters(status_, company_id, source, resume_variant_id, q, applied_from, applied_to)
    return Response(
        content=service.export_csv(user.id, filters),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="applications.csv"'},
    )


@router.post("/applications", status_code=status.HTTP_201_CREATED)
def create_application(
    body: ApplicationCreate, user: CurrentUser, service: ApplicationServiceDep
) -> ApplicationRead:
    return ApplicationRead.model_validate(service.create(user.id, body))


@router.get("/applications/{application_id}")
def get_application(
    application_id: uuid.UUID, user: CurrentUser, service: ApplicationServiceDep
) -> ApplicationRead:
    return ApplicationRead.model_validate(service.get(user.id, application_id))


@router.patch("/applications/{application_id}")
def update_application(
    application_id: uuid.UUID,
    body: ApplicationUpdate,
    user: CurrentUser,
    service: ApplicationServiceDep,
) -> ApplicationRead:
    return ApplicationRead.model_validate(service.update(user.id, application_id, body))


@router.patch(
    "/applications/{application_id}/status",
    responses={409: {"description": "Transition not allowed by the status state machine"}},
)
def change_application_status(
    application_id: uuid.UUID,
    body: StatusChangeRequest,
    user: CurrentUser,
    service: ApplicationServiceDep,
) -> ApplicationRead:
    return ApplicationRead.model_validate(
        service.change_status(user.id, application_id, body.status)
    )


@router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: uuid.UUID, user: CurrentUser, service: ApplicationServiceDep
) -> None:
    service.delete(user.id, application_id)


@router.get("/applications/{application_id}/history")
def application_history(
    application_id: uuid.UUID, user: CurrentUser, service: ApplicationServiceDep
) -> list[StatusHistoryRead]:
    return [StatusHistoryRead.model_validate(h) for h in service.history(user.id, application_id)]


@router.get("/board")
def board(user: CurrentUser, service: ApplicationServiceDep, q: SearchQ = None) -> BoardRead:
    columns = service.board(user.id, q.strip() if q and q.strip() else None)
    return BoardRead(
        columns=[
            BoardColumn(
                status=column.status,
                count=len(column.items),
                items=[ApplicationRead.model_validate(a) for a in column.items],
            )
            for column in columns
        ]
    )


# ---- nested resources --------------------------------------------------------------------
@router.get("/applications/{application_id}/interviews", tags=["interviews"])
def list_application_interviews(
    application_id: uuid.UUID, user: CurrentUser, service: InterviewServiceDep
) -> list[InterviewRead]:
    return [
        InterviewRead.model_validate(i)
        for i in service.list_for_application(user.id, application_id)
    ]


@router.post(
    "/applications/{application_id}/interviews",
    status_code=status.HTTP_201_CREATED,
    tags=["interviews"],
)
def create_interview(
    application_id: uuid.UUID,
    body: InterviewCreate,
    user: CurrentUser,
    service: InterviewServiceDep,
) -> InterviewRead:
    return InterviewRead.model_validate(service.create(user.id, application_id, body))


@router.get("/applications/{application_id}/notes", tags=["notes"])
def list_notes(
    application_id: uuid.UUID, user: CurrentUser, service: NoteServiceDep
) -> list[NoteRead]:
    return [NoteRead.model_validate(n) for n in service.list(user.id, application_id)]


@router.post(
    "/applications/{application_id}/notes",
    status_code=status.HTTP_201_CREATED,
    tags=["notes"],
)
def create_note(
    application_id: uuid.UUID, body: NoteCreate, user: CurrentUser, service: NoteServiceDep
) -> NoteRead:
    return NoteRead.model_validate(service.create(user.id, application_id, body.body))
