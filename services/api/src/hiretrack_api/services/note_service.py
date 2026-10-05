import uuid

from hiretrack_api.core.database import UnitOfWork
from hiretrack_api.core.exceptions import NotFoundError
from hiretrack_api.models import Note
from hiretrack_api.repositories.application_repository import ApplicationRepository
from hiretrack_api.repositories.note_repository import NoteRepository


class NoteService:
    def __init__(
        self, notes: NoteRepository, applications: ApplicationRepository, uow: UnitOfWork
    ) -> None:
        self._notes = notes
        self._apps = applications
        self._uow = uow

    def list(self, user_id: uuid.UUID, application_id: uuid.UUID) -> list[Note]:
        self._ensure_application(user_id, application_id)
        return self._notes.list_for_application(application_id)

    def create(self, user_id: uuid.UUID, application_id: uuid.UUID, body: str) -> Note:
        self._ensure_application(user_id, application_id)
        note = Note(application_id=application_id, body=body)
        self._notes.add(note)
        self._uow.commit()
        return note

    def delete(self, user_id: uuid.UUID, note_id: uuid.UUID) -> None:
        note = self._notes.get(user_id, note_id)
        if note is None:
            raise NotFoundError("Note not found")
        self._notes.delete(note)
        self._uow.commit()

    def _ensure_application(self, user_id: uuid.UUID, application_id: uuid.UUID) -> None:
        if self._apps.get(user_id, application_id) is None:
            raise NotFoundError("Application not found")
