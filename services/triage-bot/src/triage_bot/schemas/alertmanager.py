"""The Alertmanager webhook payload (version 4):
https://prometheus.io/docs/alerting/latest/configuration/#webhook_config"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Model(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class Alert(_Model):
    status: Literal["firing", "resolved"]
    labels: dict[str, str]
    annotations: dict[str, str] = Field(default_factory=dict)
    starts_at: datetime = Field(alias="startsAt")
    ends_at: datetime | None = Field(default=None, alias="endsAt")
    generator_url: str = Field(default="", alias="generatorURL")
    fingerprint: str = Field(min_length=1, max_length=64, pattern=r"^[0-9a-fA-F]+$")

    @property
    def name(self) -> str:
        return self.labels.get("alertname", "UnknownAlert")

    @property
    def severity(self) -> str:
        return self.labels.get("severity", "none")


class AlertmanagerWebhook(_Model):
    version: str = "4"
    status: Literal["firing", "resolved"]
    receiver: str = ""
    group_key: str = Field(default="", alias="groupKey")
    alerts: list[Alert] = Field(max_length=500)
    external_url: str = Field(default="", alias="externalURL")


class TriageResult(BaseModel):
    fingerprint: str
    alertname: str
    action: Literal["created", "duplicate", "resolved_comment", "ignored"]
    issue_url: str | None = None


class TriageResponse(BaseModel):
    results: list[TriageResult]
