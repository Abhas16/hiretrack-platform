import uuid

from fastapi import APIRouter, status

from hiretrack_api.controllers.deps import CurrentUser, NoteServiceDep

# Listing and creating notes is nested under /applications/{id}/notes (applications.py).
router = APIRouter(prefix="/notes", tags=["notes"])


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: uuid.UUID, user: CurrentUser, service: NoteServiceDep) -> None:
    service.delete(user.id, note_id)
