"""match-scorer settings. Every value comes from an environment variable of the same name."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr

from hiretrack_common.config import DatabaseSettings
from hiretrack_common.queue import QueueSettings


class ScorerSettings(DatabaseSettings, QueueSettings):
    skills_file: Path = Path("config/skills.yaml")

    # Matches below this score are not stored at all (the review queue filters further).
    match_min_score_to_store: int = Field(default=40, ge=0, le=100)

    # Port for /healthz, /readyz and /metrics (Prometheus scrapes it, probes call it).
    ops_port: int = 9100
    # /healthz fails if the worker loop hasn't ticked for this long (stuck worker -> restart).
    heartbeat_max_age_seconds: int = Field(default=300, ge=30)

    scorer_batch_size: int = Field(default=10, ge=1, le=10)
    # Long-poll wait. Keep it well under terminationGracePeriodSeconds, so SIGTERM is noticed.
    scorer_wait_seconds: int = Field(default=10, ge=0, le=20)

    # Application kit: "none" = templates (free), "anthropic" = Claude writes it.
    llm_provider: Literal["none", "anthropic"] = "none"
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-opus-5-5"
    anthropic_effort: Literal["low", "medium", "high"] = "low"
    llm_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
