"""Collect the last N minutes of context for an alert. Every source is optional: if Prometheus
or Loki is down we still file the issue and say what was missing. A triage bot that fails
during an outage (exactly when it's needed) is worse than a partial report."""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Protocol
from urllib.parse import parse_qs, urlsplit

from hiretrack_common.clock import Clock, utcnow
from triage_bot.clients import ClientError
from triage_bot.clients.promql import quote, selector
from triage_bot.metrics import ERRORS
from triage_bot.schemas.alertmanager import Alert
from triage_bot.services.context import AlertContext, LogLine, MetricSeries, PodRestarts

logger = logging.getLogger(__name__)

# Labels our log pipeline (Alloy) puts on every stream, so they can select an alert's logs.
LOG_STREAM_LABELS = ("namespace", "app", "container", "pod")
LOG_FILTER = '|~ "(?i)(error|warn|critical|exception|traceback|fault injected)"'


class Metrics(Protocol):
    def range_summary(
        self, query: str, start: datetime, end: datetime, step_seconds: int = 60
    ) -> list[MetricSeries]: ...

    def instant(self, query: str) -> list[tuple[dict[str, str], float]]: ...


class Logs(Protocol):
    def recent_lines(
        self, logql: str, start: datetime, end: datetime, limit: int
    ) -> list[LogLine]: ...


def alert_expression(generator_url: str) -> str | None:
    """Prometheus links each alert to its graph: .../graph?g0.expr=<PromQL>&g0.tab=1"""
    values = parse_qs(urlsplit(generator_url).query).get("g0.expr")
    return values[0] if values else None


class ContextGatherer:
    def __init__(
        self,
        metrics: Metrics,
        logs: Logs,
        lookback_minutes: int,
        max_log_lines: int,
        now: Clock = utcnow,
    ) -> None:
        self._metrics = metrics
        self._logs = logs
        self._lookback = lookback_minutes
        self._max_lines = max_log_lines
        self._now = now

    def gather(self, alert: Alert) -> AlertContext:
        end = self._now()
        ctx = AlertContext(window_start=end - timedelta(minutes=self._lookback), window_end=end)
        ctx.query = alert_expression(alert.generator_url)
        if ctx.query:
            self._try(ctx, "prometheus", lambda: self._add_series(ctx))

        namespace = alert.labels.get("namespace")
        if namespace:
            self._try(ctx, "prometheus", lambda: self._add_restarts(ctx, namespace))
            self._try(ctx, "loki", lambda: self._add_logs(ctx, alert.labels))
        else:
            ctx.problems.append("The alert has no namespace label, so pods and logs were skipped.")
        return ctx

    def _add_series(self, ctx: AlertContext) -> None:
        query = ctx.query or ""
        ctx.series.extend(self._metrics.range_summary(query, ctx.window_start, ctx.window_end))

    def _add_restarts(self, ctx: AlertContext, namespace: str) -> None:
        query = (
            "sum by (pod) (increase(kube_pod_container_status_restarts_total"
            f"{{namespace={quote(namespace)}}}[{self._lookback}m])) > 0"
        )
        rows = [
            PodRestarts(labels.get("pod", "?"), value)
            for labels, value in self._metrics.instant(query)
        ]
        ctx.restarts.extend(sorted(rows, key=lambda r: -r.restarts)[:10])

    def _add_logs(self, ctx: AlertContext, labels: dict[str, str]) -> None:
        stream = {key: labels[key] for key in LOG_STREAM_LABELS if labels.get(key)}
        logql = f"{selector(stream)} {LOG_FILTER}"
        ctx.logs.extend(
            self._logs.recent_lines(logql, ctx.window_start, ctx.window_end, self._max_lines)
        )

    @staticmethod
    def _try(ctx: AlertContext, stage: str, action: Callable[[], None]) -> None:
        try:
            action()
        except ClientError as exc:
            ERRORS.labels(stage).inc()
            ctx.problems.append(f"{stage} unavailable: {exc}")
            logger.warning("context source failed", extra={"stage": stage, "error": str(exc)})
