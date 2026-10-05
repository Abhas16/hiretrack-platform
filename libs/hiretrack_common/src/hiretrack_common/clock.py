"""One place to get the current time, so services can take a fake clock in tests."""

from collections.abc import Callable
from datetime import UTC, datetime

type Clock = Callable[[], datetime]


def utcnow() -> datetime:
    return datetime.now(UTC)
