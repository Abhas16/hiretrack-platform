"""What triage-bot collects about an alert, as plain data (built by clients, read by the
analysis and the issue renderer)."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class MetricSeries:
    labels: dict[str, str]
    last: float
    minimum: float
    maximum: float


@dataclass(frozen=True)
class PodRestarts:
    pod: str
    restarts: float


@dataclass(frozen=True)
class LogLine:
    timestamp: datetime
    pod: str
    line: str


@dataclass
class AlertContext:
    window_start: datetime
    window_end: datetime
    query: str | None = None  # the alert's own PromQL, from its generatorURL
    series: list[MetricSeries] = field(default_factory=list)
    restarts: list[PodRestarts] = field(default_factory=list)
    logs: list[LogLine] = field(default_factory=list)
    # A source that failed is noted here instead of failing the whole triage.
    problems: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Analysis:
    cause: str
    next_steps: list[str]
    provider: str  # "rules" or "anthropic"
    rule: str | None = None
