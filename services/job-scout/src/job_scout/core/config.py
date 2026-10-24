"""job-scout settings. Every value comes from an environment variable of the same name."""

from pathlib import Path

from pydantic import Field

from hiretrack_common.config import DatabaseSettings
from hiretrack_common.queue import QueueSettings

DEFAULT_USER_AGENT = (
    "HireTrackScout/0.1 (+https://github.com/Abhas16/hiretrack-platform; personal job search)"
)


class ScoutSettings(DatabaseSettings, QueueSettings):
    sources_file: Path = Path("config/sources.yaml")

    # Politeness: these are other companies' servers, so go slow and identify ourselves.
    scout_user_agent: str = DEFAULT_USER_AGENT
    scout_request_delay_seconds: float = Field(default=1.0, ge=0)  # min gap per host
    scout_request_timeout_seconds: float = Field(default=15.0, gt=0, le=120)
    scout_max_retries: int = Field(default=3, ge=0, le=10)
    scout_backoff_base_seconds: float = Field(default=2.0, ge=0)
    scout_max_description_chars: int = Field(default=20_000, ge=1000)

    # CronJob pods exit after each run, so metrics are pushed instead of scraped.
    pushgateway_url: str | None = None
