"""The CronJob's main: wire everything, run once, push metrics, exit 0 (ok) or 1 (failed).

The exit code matters: Kubernetes marks the Job failed on non-zero, and kube-state-metrics
exposes that (kube_job_status_failed) for alerting, on top of scout_last_success_timestamp.
"""

import logging
import time

import httpx

from hiretrack_common.db import create_db_engine, create_session_factory
from hiretrack_common.logging import configure_logging
from hiretrack_common.metrics import push_metrics
from hiretrack_common.queue import build_queue
from job_scout import __version__
from job_scout.core.config import ScoutSettings
from job_scout.core.sources_config import load_sources
from job_scout.metrics import LAST_SUCCESS, REGISTRY, RUN_DURATION
from job_scout.repositories.job_repository import JobRepository
from job_scout.services.scout_service import ScoutService
from job_scout.sources import PoliteHttpClient, build_boards

logger = logging.getLogger("job_scout")


def run(settings: ScoutSettings | None = None) -> int:
    settings = settings or ScoutSettings()  # DB_PASSWORD etc. come from the environment
    configure_logging("job-scout", settings.log_level, settings.log_format)
    started = time.perf_counter()
    config = load_sources(settings.sources_file)
    logger.info(
        "scout run starting", extra={"sources": len(config.sources), "version": __version__}
    )

    engine = create_db_engine(settings)
    session = create_session_factory(engine)()
    timeout = httpx.Timeout(settings.scout_request_timeout_seconds)
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            http = PoliteHttpClient(
                client,
                user_agent=settings.scout_user_agent,
                delay_seconds=settings.scout_request_delay_seconds,
                max_retries=settings.scout_max_retries,
                backoff_base_seconds=settings.scout_backoff_base_seconds,
            )
            service = ScoutService(
                boards=build_boards(http, settings.scout_max_description_chars),
                jobs=JobRepository(session),
                commit=session.commit,
                queue=build_queue(settings),
            )
            result = service.run(config)
    except Exception:
        logger.exception("scout run crashed")
        RUN_DURATION.set(time.perf_counter() - started)
        push_metrics(settings.pushgateway_url, "job-scout", REGISTRY)
        return 1
    finally:
        session.close()
        engine.dispose()

    ok = result.succeeded(len(config.sources))
    RUN_DURATION.set(time.perf_counter() - started)
    if ok:
        LAST_SUCCESS.set_to_current_time()
    push_metrics(settings.pushgateway_url, "job-scout", REGISTRY)
    logger.info(
        "scout run finished" if ok else "scout run failed",
        extra={
            "fetched": result.fetched,
            "new": result.new,
            "published": result.published,
            "failed_sources": result.failed_sources,
            "publish_error": result.publish_error,
        },
    )
    return 0 if ok else 1
