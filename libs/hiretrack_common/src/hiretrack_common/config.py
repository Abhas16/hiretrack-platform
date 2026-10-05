"""Settings shared by every service. Everything comes from environment variables."""

from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class BaseServiceSettings(BaseSettings):
    """Settings every service has. A local `.env` file is read for development only."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["local", "test", "dev", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


class DatabaseSettings(BaseServiceSettings):
    """PostgreSQL connection settings. Only DB_PASSWORD is a secret."""

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "hiretrack"
    db_user: str = "hiretrack"
    db_password: SecretStr
    db_sslmode: Literal["disable", "allow", "prefer", "require", "verify-ca", "verify-full"] = (
        "prefer"
    )
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=5, ge=0)
    db_connect_timeout_seconds: int = Field(default=5, ge=1)

    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={
                "sslmode": self.db_sslmode,
                "connect_timeout": str(self.db_connect_timeout_seconds),
            },
        )
