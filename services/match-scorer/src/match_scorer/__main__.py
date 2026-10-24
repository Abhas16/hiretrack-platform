"""Entry point: `python -m match_scorer` (what the Deployment's container runs).

Wiring only: settings -> logging -> DB, queue, taxonomy, kit writer -> ops server -> loop.
One DB session per message, so a failed message can't leave a broken session behind.
"""

import logging
import uuid
from functools import partial

from hiretrack_common.db import create_db_engine, create_session_factory, ping
from hiretrack_common.logging import configure_logging
from hiretrack_common.ops_server import Heartbeat, OpsServer
from hiretrack_common.queue import build_queue
from hiretrack_common.shutdown import ShutdownSignal
from hiretrack_common.skills import SkillTaxonomy
from match_scorer import __version__
from match_scorer.consumers.job_consumer import JobConsumer
from match_scorer.core.config import ScorerSettings
from match_scorer.repositories.match_repository import MatchRepository
from match_scorer.services.kit_factory import build_kit_writer
from match_scorer.services.match_service import MatchService

logger = logging.getLogger("match_scorer")


def main() -> None:
    settings = ScorerSettings()  # DB_PASSWORD etc. come from the environment
    configure_logging("match-scorer", settings.log_level, settings.log_format)

    engine = create_db_engine(settings)
    sessions = create_session_factory(engine)
    queue = build_queue(settings)
    taxonomy = SkillTaxonomy.load(settings.skills_file)
    kit_writer = build_kit_writer(settings)

    def handle(job_id: uuid.UUID) -> int:
        with sessions() as session:
            service = MatchService(
                MatchRepository(session),
                commit=session.commit,
                release=session.rollback,
                taxonomy=taxonomy,
                kit_writer=kit_writer,
                min_score=settings.match_min_score_to_store,
            )
            return service.process(job_id)

    shutdown = ShutdownSignal()
    shutdown.install()
    heartbeat = Heartbeat(settings.heartbeat_max_age_seconds)
    ops = OpsServer(
        settings.ops_port, heartbeat, {"database": partial(ping, engine), "queue": queue.ping}
    )
    ops.start()
    logger.info(
        "match-scorer started",
        extra={
            "version": __version__,
            "queue": settings.queue_backend,
            "kit": settings.llm_provider,
        },
    )
    try:
        JobConsumer(
            queue,
            handle,
            shutdown,
            heartbeat,
            batch_size=settings.scorer_batch_size,
            wait_seconds=settings.scorer_wait_seconds,
        ).run()
    finally:
        ops.stop()
        engine.dispose()


if __name__ == "__main__":
    main()
