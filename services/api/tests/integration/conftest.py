"""Integration fixtures: a throwaway Postgres in Docker, migrated with Alembic, per test session."""

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import Engine, create_engine, text
from testcontainers.postgres import PostgresContainer

from hiretrack_api.core.config import ApiSettings
from hiretrack_api.main import create_app

API_DIR = Path(__file__).resolve().parents[2]
PASSWORD = "integration-test-only"

type AuthHeaders = dict[str, str]


@pytest.fixture(scope="session")
def postgres() -> Iterator[PostgresContainer]:
    container = PostgresContainer(
        "postgres:16-alpine", username="hiretrack", password=PASSWORD, dbname="hiretrack"
    )
    try:
        container.start()
    except Exception as exc:  # Docker not running / not installed
        pytest.skip(f"Docker is not available for integration tests: {exc}")
    yield container
    container.stop()


@pytest.fixture(scope="session")
def settings(postgres: PostgresContainer) -> ApiSettings:
    return ApiSettings(
        db_host=postgres.get_container_host_ip(),
        db_port=int(postgres.get_exposed_port(5432)),
        db_name="hiretrack",
        db_user="hiretrack",
        db_password=SecretStr(PASSWORD),
        db_sslmode="disable",
        jwt_secret=SecretStr("integration-test-secret-0123456789abcdef"),
        app_env="test",
        log_format="console",
    )


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    return Config(str(API_DIR / "alembic.ini"))


@pytest.fixture(scope="session")
def engine(settings: ApiSettings, alembic_config: Config) -> Iterator[Engine]:
    engine = create_engine(settings.database_url())
    with engine.begin() as connection:
        alembic_config.attributes["connection"] = connection
        command.upgrade(alembic_config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def client(settings: ApiSettings, engine: Engine) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client
    with engine.begin() as connection:
        # Every table hangs off users, so this empties the database between tests.
        connection.execute(text("TRUNCATE users CASCADE"))


@pytest.fixture
def register(client: TestClient) -> Callable[[str], AuthHeaders]:
    """Register + log in a user; returns ready-to-use Authorization headers."""

    def _register(email: str) -> AuthHeaders:
        password = "correct-horse-battery"
        response = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Test User"},
        )
        assert response.status_code == 201, response.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200, login.text
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return _register


@pytest.fixture
def auth(register: Callable[[str], AuthHeaders]) -> AuthHeaders:
    return register("abhas@example.com")
