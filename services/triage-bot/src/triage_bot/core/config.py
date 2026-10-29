"""triage-bot settings. Every value comes from an environment variable of the same name."""

from typing import Literal

from pydantic import Field, SecretStr, field_validator

from hiretrack_common.config import BaseServiceSettings


class TriageSettings(BaseServiceSettings):
    host: str = "0.0.0.0"  # noqa: S104 - must listen on all interfaces inside a container
    port: int = 8080

    # Shared secret Alertmanager sends as "Authorization: Bearer <token>" (http_config).
    webhook_token: SecretStr

    # GitHub: a fine-grained token with "Issues: read and write" on ONE repo.
    # Without both values the bot runs in dry-run mode: it logs the issue instead.
    github_repo: str | None = None  # "owner/name"
    github_token: SecretStr | None = None
    github_api_url: str = "https://api.github.com"
    issue_labels: str = "incident,triage-bot"  # comma-separated; severity:<x> is added too

    # In-cluster service URLs (kube-prometheus-stack and Loki).
    prometheus_url: str = "http://localhost:9090"
    loki_url: str = "http://localhost:3100"
    lookback_minutes: int = Field(default=15, ge=1, le=360)
    max_log_lines: int = Field(default=20, ge=1, le=200)
    http_timeout_seconds: float = Field(default=5.0, gt=0, le=30)

    # Used when an alert has no runbook_url annotation: <base>/<alertname>.md
    runbook_base_url: str = ""

    # Probable-cause analysis: "none" = built-in rules (default), "anthropic" = Claude.
    llm_provider: Literal["none", "anthropic"] = "none"
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-opus-5-5"
    anthropic_effort: Literal["low", "medium", "high"] = "low"
    llm_timeout_seconds: float = Field(default=30.0, gt=0, le=120)

    @field_validator("webhook_token")
    @classmethod
    def _token_long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 24:
            raise ValueError("WEBHOOK_TOKEN must be at least 24 characters")
        return value

    @property
    def dry_run(self) -> bool:
        return not (self.github_repo and self.github_token)

    @property
    def labels(self) -> list[str]:
        return [label.strip() for label in self.issue_labels.split(",") if label.strip()]
