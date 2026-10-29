from pydantic import Field

from hiretrack_common.config import DatabaseSettings


class ReminderSettings(DatabaseSettings):
    # An APPLIED application with no status change or edit for this many days gets a follow-up.
    follow_up_after_days: int = Field(default=7, ge=1, le=90)
    # CronJob pods exit after each run, so metrics are pushed instead of scraped.
    pushgateway_url: str | None = None
