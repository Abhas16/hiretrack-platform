import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from hiretrack_api.models import PracticeSession


class PracticeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, user_id: uuid.UUID, limit: int) -> list[PracticeSession]:
        stmt = (
            select(PracticeSession)
            .options(selectinload(PracticeSession.turns))
            .where(PracticeSession.user_id == user_id)
            .order_by(PracticeSession.created_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt))

    def get(self, user_id: uuid.UUID, session_id: uuid.UUID) -> PracticeSession | None:
        stmt = (
            select(PracticeSession)
            .options(selectinload(PracticeSession.turns))
            .where(PracticeSession.user_id == user_id, PracticeSession.id == session_id)
        )
        return self._session.scalar(stmt)

    def add(self, practice_session: PracticeSession) -> None:
        self._session.add(practice_session)
        self._session.flush()

    def delete(self, practice_session: PracticeSession) -> None:
        self._session.delete(practice_session)
        self._session.flush()
