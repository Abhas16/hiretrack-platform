import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query, status

from hiretrack_api.controllers.deps import CurrentUser, ReminderServiceDep
from hiretrack_api.schemas.reminder import ReminderCreate, ReminderRead, ReminderUpdate
from hiretrack_common.domain.enums import ReminderStatus

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("")
def list_reminders(
    user: CurrentUser,
    service: ReminderServiceDep,
    status_: Annotated[ReminderStatus | None, Query(alias="status")] = None,
    due_before: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ReminderRead]:
    return [
        ReminderRead.model_validate(r) for r in service.list(user.id, status_, due_before, limit)
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_reminder(
    body: ReminderCreate, user: CurrentUser, service: ReminderServiceDep
) -> ReminderRead:
    return ReminderRead.model_validate(service.create(user.id, body))


@router.patch("/{reminder_id}")
def update_reminder(
    reminder_id: uuid.UUID, body: ReminderUpdate, user: CurrentUser, service: ReminderServiceDep
) -> ReminderRead:
    return ReminderRead.model_validate(service.update(user.id, reminder_id, body))


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: uuid.UUID, user: CurrentUser, service: ReminderServiceDep) -> None:
    service.delete(user.id, reminder_id)
