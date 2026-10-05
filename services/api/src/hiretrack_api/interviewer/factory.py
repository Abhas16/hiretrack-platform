"""Build the interviewer from settings, wrapping the LLM in a fallback to the rule-based one."""

import logging

import anthropic

from hiretrack_api.core.config import ApiSettings
from hiretrack_api.interviewer.anthropic_provider import AnthropicInterviewer
from hiretrack_api.interviewer.base import Evaluation, Interviewer, InterviewerError, Question
from hiretrack_api.interviewer.metrics import FALLBACKS
from hiretrack_api.interviewer.rule_based import RuleBasedInterviewer

logger = logging.getLogger(__name__)


class FallbackInterviewer:
    """Try the primary interviewer; on any InterviewerError use the fallback instead."""

    def __init__(self, primary: Interviewer, fallback: Interviewer) -> None:
        self.name = primary.name
        self._primary = primary
        self._fallback = fallback

    def generate_questions(self, role: str, topics: list[str], count: int) -> list[Question]:
        try:
            return self._primary.generate_questions(role, topics, count)
        except InterviewerError as exc:
            self._log_fallback("generate", exc)
            return self._fallback.generate_questions(role, topics, count)

    def evaluate(self, role: str, question: Question, answer: str) -> Evaluation:
        try:
            return self._primary.evaluate(role, question, answer)
        except InterviewerError as exc:
            self._log_fallback("evaluate", exc)
            return self._fallback.evaluate(role, question, answer)

    def _log_fallback(self, operation: str, exc: InterviewerError) -> None:
        FALLBACKS.labels(operation).inc()
        logger.warning(
            "interviewer fell back to rule-based",
            extra={"operation": operation, "reason": str(exc)},
        )


def build_interviewer(settings: ApiSettings) -> Interviewer:
    rule_based = RuleBasedInterviewer()
    if settings.llm_provider != "anthropic":
        return rule_based

    key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None
    client = anthropic.Anthropic(
        api_key=key,  # None -> the SDK reads ANTHROPIC_API_KEY from the environment
        timeout=settings.llm_timeout_seconds,
        max_retries=1,  # keep the user waiting at most ~2x the timeout before falling back
    )
    llm = AnthropicInterviewer(client, settings.anthropic_model, settings.anthropic_effort)
    return FallbackInterviewer(llm, rule_based)
