import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from hiretrack_api.models import Application, Note


class NoteRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_application(self, application_id: uuid.UUID) -> list[Note]:
        stmt = (
            select(Note)
            .where(Note.application_id == application_id)
            .order_by(Note.created_at.desc())
        )
        return list(self._session.scalars(stmt))

    def get(self, user_id: uuid.UUID, note_id: uuid.UUID) -> Note | None:
        stmt = (
            select(Note)
            .join(Application, Application.id == Note.application_id)
            .where(Note.id == note_id, Application.user_id == user_id)
        )
        return self._session.scalar(stmt)

    def add(self, note: Note) -> None:
        self._session.add(note)
        self._session.flush()

    def delete(self, note: Note) -> None:
        self._session.delete(note)
        self._session.flush()
