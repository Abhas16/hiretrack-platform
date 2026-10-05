"""Alembic environment.

Only DatabaseSettings are loaded (not ApiSettings), so the migration Job needs just the DB_*
variables — no JWT secret. Tests can pass an open connection via config.attributes.
"""

import logging

from alembic import context
from sqlalchemy import Connection, create_engine, pool

import hiretrack_common.db.models  # noqa: F401  (registers every table on Base.metadata)
from hiretrack_common.config import DatabaseSettings
from hiretrack_common.db import Base

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

config = context.config
target_metadata = Base.metadata


def _configure(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )


def run_migrations_offline() -> None:
    """`alembic upgrade head --sql`: print the SQL instead of running it (useful for review)."""
    url = DatabaseSettings().database_url()
    context.configure(
        url=url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection: Connection | None = config.attributes.get("connection")
    if connection is not None:
        _configure(connection)
        with context.begin_transaction():
            context.run_migrations()
        return

    engine = create_engine(DatabaseSettings().database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        _configure(connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
