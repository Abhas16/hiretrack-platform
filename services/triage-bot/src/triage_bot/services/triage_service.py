"""One webhook = a group of alerts. For each one:

  firing   + no open issue  -> gather context, analyse, open an issue
  firing   + open issue     -> nothing (Alertmanager re-sends every repeat_interval)
  resolved + open issue     -> comment "resolved" (left open for the follow-up)
  resolved + no issue       -> nothing

GitHub failures propagate (the controller answers 502), so Alertmanager retries the webhook;
the fingerprint check makes that retry safe.
"""

import logging
import time
from typing import Literal

from triage_bot.clients.github import IssueTracker
from triage_bot.metrics import ALERTS_HANDLED, PROCESSING_SECONDS
from triage_bot.schemas.alertmanager import Alert, AlertmanagerWebhook, TriageResult
from triage_bot.services.gatherer import ContextGatherer
from triage_bot.services.llm_analyst import Analyzer
from triage_bot.services.report import issue_body, issue_title, resolved_comment, runbook_url

logger = logging.getLogger(__name__)

type Action = Literal["created", "duplicate", "resolved_comment", "ignored"]


class TriageService:
    def __init__(
        self,
        gatherer: ContextGatherer,
        analyze: Analyzer,
        issues: IssueTracker,
        labels: list[str],
        runbook_base_url: str,
    ) -> None:
        self._gatherer = gatherer
        self._analyze = analyze
        self._issues = issues
        self._labels = labels
        self._runbook_base = runbook_base_url

    def handle(self, webhook: AlertmanagerWebhook) -> list[TriageResult]:
        return [self._handle_one(alert) for alert in webhook.alerts]

    def _handle_one(self, alert: Alert) -> TriageResult:
        started = time.perf_counter()
        existing = self._issues.find_open(alert.fingerprint)

        if alert.status == "resolved":
            if existing is None:
                return self._result(alert, "ignored")
            self._issues.comment(existing, resolved_comment(alert))
            return self._result(alert, "resolved_comment", existing.url)

        if existing is not None:
            return self._result(alert, "duplicate", existing.url)

        ctx = self._gatherer.gather(alert)
        analysis = self._analyze(alert, ctx)
        body = issue_body(alert, ctx, analysis, runbook_url(alert, self._runbook_base))
        labels = [*self._labels, f"severity:{alert.severity}"]
        issue = self._issues.create(alert.fingerprint, issue_title(alert), body, labels)
        PROCESSING_SECONDS.observe(time.perf_counter() - started)
        logger.info(
            "incident issue opened",
            extra={"alertname": alert.name, "issue": issue.url, "rule": analysis.rule},
        )
        return self._result(alert, "created", issue.url)

    @staticmethod
    def _result(alert: Alert, action: Action, url: str | None = None) -> TriageResult:
        ALERTS_HANDLED.labels(action).inc()
        return TriageResult(
            fingerprint=alert.fingerprint,
            alertname=alert.name,
            action=action,
            issue_url=url,
        )
