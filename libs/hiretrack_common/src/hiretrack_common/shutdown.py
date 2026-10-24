"""Graceful shutdown for workers.

On scale-down or a rollout, Kubernetes sends SIGTERM, then waits terminationGracePeriodSeconds,
then SIGKILL. Workers must finish the message in hand, ack it, and exit before that deadline;
a killed worker isn't fatal (the message is redelivered) but it costs a retry.
"""

import logging
import signal
import threading
from types import FrameType

logger = logging.getLogger(__name__)


class ShutdownSignal:
    def __init__(self) -> None:
        self._event = threading.Event()

    def install(self) -> None:
        """Call from the main thread (Python only delivers signals there)."""
        signal.signal(signal.SIGTERM, self._handle)
        signal.signal(signal.SIGINT, self._handle)

    def _handle(self, signum: int, _frame: FrameType | None) -> None:
        logger.info("shutdown requested", extra={"signal": signal.Signals(signum).name})
        self._event.set()

    def request(self) -> None:
        self._event.set()

    @property
    def requested(self) -> bool:
        return self._event.is_set()
