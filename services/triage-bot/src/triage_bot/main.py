"""Application factory: settings -> clients -> analysis -> service -> routes."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anthropic
import httpx
from fastapi import FastAPI

from hiretrack_common.logging import configure_logging
from triage_bot import __version__
from triage_bot.clients.github import DryRunIssues, GitHubIssues, IssueTracker
from triage_bot.clients.loki import LokiClient
from triage_bot.clients.prometheus import PrometheusClient
from triage_bot.controllers import ops, webhooks
from triage_bot.core.config import TriageSettings
from triage_bot.services import cause_rules
from triage_bot.services.gatherer import ContextGatherer
from triage_bot.services.llm_analyst import Analyzer, LlmAnalyst
from triage_bot.services.triage_service import TriageService

logger = logging.getLogger(__name__)


def build_analyzer(settings: TriageSettings) -> Analyzer:
    if settings.llm_provider != "anthropic":
        return cause_rules.analyze
    key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None
    client = anthropic.Anthropic(api_key=key, timeout=settings.llm_timeout_seconds, max_retries=1)
    return LlmAnalyst(
        client, settings.anthropic_model, settings.anthropic_effort, cause_rules.analyze
    )


def build_issue_tracker(settings: TriageSettings, http: httpx.Client) -> IssueTracker:
    if settings.dry_run or not settings.github_token or not settings.github_repo:
        logger.warning("GITHUB_TOKEN/GITHUB_REPO not set: dry run, issues are only logged")
        return DryRunIssues()
    return GitHubIssues(
        http,
        settings.github_api_url,
        settings.github_repo,
        settings.github_token.get_secret_value(),
    )


def create_app(settings: TriageSettings, service: TriageService | None = None) -> FastAPI:
    """`service` lets tests inject fakes; production builds the real one here."""
    configure_logging("triage-bot", settings.log_level, settings.log_format)
    http = httpx.Client(timeout=settings.http_timeout_seconds)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info(
            "triage-bot started", extra={"version": __version__, "dry_run": settings.dry_run}
        )
        yield
        http.close()

    app = FastAPI(
        title="HireTrack triage-bot",
        version=__version__,
        lifespan=lifespan,
        docs_url=None if settings.app_env == "prod" else "/docs",
        redoc_url=None,
    )
    app.state.settings = settings
    app.state.triage_service = service or TriageService(
        ContextGatherer(
            PrometheusClient(http, settings.prometheus_url),
            LokiClient(http, settings.loki_url),
            settings.lookback_minutes,
            settings.max_log_lines,
        ),
        build_analyzer(settings),
        build_issue_tracker(settings, http),
        settings.labels,
        settings.runbook_base_url,
    )
    app.include_router(ops.router)
    app.include_router(webhooks.router)
    return app
