"""The migrations and the ORM models must describe the same schema."""

import uuid
from datetime import UTC, datetime

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import hiretrack_common.db.models  # noqa: F401
from hiretrack_api.models import Application, Company, Reminder, User
from hiretrack_common.db import Base
from hiretrack_common.domain.enums import ReminderCreatedBy, ReminderKind

pytestmark = pytest.mark.integration


def test_models_match_migrations(engine: Engine) -> None:
    """Fails if someone changes a model and forgets `alembic revision --autogenerate`."""
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []


def test_downgrade_to_base_and_upgrade_again(engine: Engine, alembic_config: Config) -> None:
    with engine.begin() as connection:
        alembic_config.attributes["connection"] = connection
        command.downgrade(alembic_config, "base")
        command.upgrade(alembic_config, "head")


def test_only_one_open_follow_up_per_application(engine: Engine) -> None:
    """The partial unique index that makes the reminder-worker safe to run twice."""
    with Session(engine) as session:
        user = User(email=f"{uuid.uuid4()}@example.com", password_hash="x", full_name="T")
        session.add(user)
        session.flush()
        company = Company(user_id=user.id, name="Swiggy")
        session.add(company)
        session.flush()
        application = Application(user_id=user.id, company_id=company.id, role="Platform Engineer")
        session.add(application)
        session.flush()

        def follow_up() -> Reminder:
            return Reminder(
                user_id=user.id,
                application_id=application.id,
                kind=ReminderKind.FOLLOW_UP,
                created_by=ReminderCreatedBy.WORKER,
                message="Follow up",
                due_at=datetime.now(UTC),
            )

        session.add(follow_up())
        session.flush()
        session.add(follow_up())
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()
