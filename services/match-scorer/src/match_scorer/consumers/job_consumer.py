"""The worker loop: receive -> handle -> ack. The "controller" of a queue worker.

success          -> ack (message deleted)
handler raised   -> NO ack: the message becomes visible again after the visibility timeout
                    and is retried; after QUEUE_MAX_RECEIVES tries it lands in the DLQ
malformed body   -> ack and log: retrying can never fix it, so don't waste 5 attempts
SIGTERM          -> finish the current message, stop taking new ones, exit
"""

import logging
import time
import uuid
from collections.abc import Callable

from hiretrack_common.ops_server import Heartbeat
from hiretrack_common.queue import Message, Queue, QueueError
from hiretrack_common.queue.metrics import QUEUE_MESSAGES_FAILED
from hiretrack_common.shutdown import ShutdownSignal
from match_scorer.metrics import JOBS_PROCESSED, PROCESSING_SECONDS

logger = logging.getLogger(__name__)

QUEUE_ERROR_BACKOFF_SECONDS = 5.0

type Handler = Callable[[uuid.UUID], int]


class JobConsumer:
    def __init__(
        self,
        queue: Queue,
        handler: Handler,
        shutdown: ShutdownSignal,
        heartbeat: Heartbeat,
        batch_size: int = 10,
        wait_seconds: int = 10,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._queue = queue
        self._handle_job = handler
        self._shutdown = shutdown
        self._heartbeat = heartbeat
        self._batch = batch_size
        self._wait = wait_seconds
        self._sleep = sleep

    def run(self) -> None:
        logger.info("consumer started", extra={"queue": self._queue.name})
        while not self._shutdown.requested:
            self._heartbeat.beat()
            try:
                messages = self._queue.receive(self._batch, self._wait)
            except QueueError as exc:
                # Queue briefly unreachable: /readyz turns red, we wait and try again.
                logger.warning("receive failed", extra={"error": str(exc)})
                self._sleep(QUEUE_ERROR_BACKOFF_SECONDS)
                continue
            for message in messages:
                if self._shutdown.requested:
                    break  # unhandled messages are redelivered to another worker
                self.handle(message)
                self._heartbeat.beat()
        logger.info("consumer stopped")

    def handle(self, message: Message) -> None:
        started = time.perf_counter()
        try:
            job_id = uuid.UUID(str(message.body["job_id"]))
        except (KeyError, ValueError):
            logger.error("dropping malformed message", extra={"message_id": message.id})
            JOBS_PROCESSED.labels("invalid").inc()
            self._safe_ack(message)
            return

        try:
            self._handle_job(job_id)
        except Exception:
            QUEUE_MESSAGES_FAILED.labels(self._queue.name).inc()
            JOBS_PROCESSED.labels("error").inc()
            logger.exception(
                "processing failed, will be retried",
                extra={
                    "job_id": str(job_id),
                    "message_id": message.id,
                    "receive_count": message.receive_count,
                },
            )
            return
        finally:
            PROCESSING_SECONDS.observe(time.perf_counter() - started)

        JOBS_PROCESSED.labels("ok").inc()
        self._safe_ack(message)

    def _safe_ack(self, message: Message) -> None:
        try:
            self._queue.ack(message)
        except QueueError as exc:
            # The work is done; if the ack is lost the message comes back and the
            # idempotent handler turns the repeat into a no-op.
            logger.warning("ack failed", extra={"message_id": message.id, "error": str(exc)})
