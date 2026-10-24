"""The interface every queue backend implements, so services never import redis or boto3."""

from dataclasses import dataclass
from typing import Any, Protocol


class QueueError(Exception):
    """The backend could not be reached or rejected the request."""


@dataclass(frozen=True)
class Message:
    id: str
    body: dict[str, Any]
    receive_count: int  # 1 on first delivery; > 1 means an earlier attempt failed or timed out
    receipt: str  # backend handle needed to ack (SQS receipt handle / Redis stream entry ID)


class Queue(Protocol):
    name: str

    def publish(self, body: dict[str, Any]) -> None: ...

    def publish_many(self, bodies: list[dict[str, Any]]) -> None: ...

    def receive(self, max_messages: int = 10, wait_seconds: int = 10) -> list[Message]:
        """Block up to wait_seconds for messages. Received messages are hidden from other
        consumers until acked, or until the visibility timeout ends (then redelivered)."""
        ...

    def ack(self, message: Message) -> None:
        """Done: delete the message for good."""
        ...

    def ping(self) -> None:
        """Raise QueueError if the queue is unusable. Used by /readyz."""
        ...
