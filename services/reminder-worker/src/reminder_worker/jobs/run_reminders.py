"""The CronJob's main: run once, push metrics, exit 0 (ok) or 1 (failed)."""

import logging
import time

from hiretrack_common.db import create_db_engine, create_session_factory
from hiretrack_common.logging import configure_logging
from hiretrack_common.metrics import push_metrics
from reminder_worker import __version__
from reminder_worker.core.config import ReminderSettings
from reminder_worker.metrics import LAST_SUCCESS, REGISTRY, RUN_DURATION
from reminder_worker.repositories.follow_up_repository import FollowUpRepository
from reminder_worker.services.follow_up_service import FollowUpService

logger = logging.getLogger("reminder_worker")


def run(settings: ReminderSettings | None = None) -> int:
    settings = settings or ReminderSettings()  # DB_PASSWORD etc. come from the environment
    configure_logging("reminder-worker", settings.log_level, settings.log_format)
    logger.info("reminder run starting", extra={"version": __version__})
    started = time.perf_counter()
    engine = create_db_engine(settings)
    exit_code = 0
    try:
        with create_session_factory(engine)() as session:
            service = FollowUpService(
                FollowUpRepository(session), session.commit, settings.follow_up_after_days
            )
            service.run()
        LAST_SUCCESS.set_to_current_time()
    except Exception:
        logger.exception("reminder run failed")
        exit_code = 1
    finally:
        engine.dispose()
        RUN_DURATION.set(time.perf_counter() - started)
        push_metrics(settings.pushgateway_url, "reminder-worker", REGISTRY)
    return exit_code
