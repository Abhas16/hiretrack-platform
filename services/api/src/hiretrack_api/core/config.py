"""API settings. Every value comes from an environment variable of the same name (upper-case)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator

from hiretrack_common.config import DatabaseSettings


class ApiSettings(DatabaseSettings):
    host: str = "0.0.0.0"  # noqa: S104 - must listen on all interfaces inside a container
    port: int = 8000

    jwt_secret: SecretStr
    jwt_issuer: str = "hiretrack-api"
    jwt_access_ttl_minutes: int = Field(default=60, ge=5, le=1440)

    cors_allowed_origins: str = ""  # comma-separated, e.g. "http://localhost:5173"
    allow_registration: bool = True

    # Chaos testing: fraction of /api/* requests answered with an injected 500.
    fault_injection_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    # Seconds uvicorn waits for in-flight requests after SIGTERM before exiting.
    shutdown_grace_seconds: int = Field(default=20, ge=0)

    # Practice interviewer: "none" = built-in question bank (free), "anthropic" = Claude.
    llm_provider: Literal["none", "anthropic"] = "none"
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-opus-5-5"
    anthropic_effort: Literal["low", "medium", "high"] = "low"
    llm_timeout_seconds: float = Field(default=30.0, gt=0, le=120)

    @field_validator("jwt_secret")
    @classmethod
    def _secret_long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> ApiSettings:
    return ApiSettings()  # required fields (DB_PASSWORD, JWT_SECRET) come from the environment
