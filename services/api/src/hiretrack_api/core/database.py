"""Per-request database session and the transaction boundary used by services."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session


def get_session(request: Request) -> Iterator[Session]:
    """FastAPI dependency: one session per request, always closed, rolled back on error."""
    session: Session = request.app.state.session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class UnitOfWork:
    """The service layer decides when a transaction commits. Repositories only add/flush."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def commit(self) -> None:
        self._session.commit()

    def release(self) -> None:
        """End the current (read-only) transaction so its DB connection goes back to the pool.

        Call before slow external work, e.g. an LLM request: otherwise every waiting request
        holds a connection, and a few slow calls can exhaust the pool for the whole API.
        Loaded objects are expired, so re-read anything needed afterwards.
        """
        self._session.rollback()
