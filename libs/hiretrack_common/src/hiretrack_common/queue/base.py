"""The interface every queue backend implements, so services never import redis or boto3."""

import json
from dataclasses import dataclass
from typing import Any, Protocol


class QueueError(Exception):
    """The backend could not be reached or rejected the request."""


UNPARSEABLE_KEY = "_unparseable"


def parse_body(raw: str) -> dict[str, Any]:
    """Decode a message body without ever raising. A body that isn't a JSON object becomes
    {"_unparseable": <start of the text>}: the consumer then treats it as malformed instead of
    crashing the worker (which would crash-loop on the same message until the DLQ)."""
    try:
        body = json.loads(raw)
    except ValueError:
        return {UNPARSEABLE_KEY: raw[:200]}
    return body if isinstance(body, dict) else {UNPARSEABLE_KEY: raw[:200]}


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
