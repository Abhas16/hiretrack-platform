"""Engine and session factory built from DatabaseSettings."""

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from hiretrack_common.config import DatabaseSettings


def create_db_engine(settings: DatabaseSettings) -> Engine:
    return create_engine(
        settings.database_url(),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,  # drop dead connections (e.g. after an RDS failover) before use
        pool_recycle=1800,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    # expire_on_commit=False: objects stay readable after commit, for building the response.
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def ping(engine: Engine) -> None:
    """Raise if the database can't answer a trivial query. Used by readiness checks."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
