"""Redis Streams backend, for local development and docker-compose.

Mapping to SQS ideas:
  send message        -> XADD
  receive (hidden)    -> XREADGROUP with a consumer group (entry goes to the Pending Entries List)
  delete              -> XACK + XDEL
  visibility timeout  -> XAUTOCLAIM re-delivers pending entries idle for longer than the timeout
  redrive to DLQ      -> done here: after max_receives deliveries, XADD to "<stream>-dlq"
"""

import json
import logging
import socket
from typing import Any

import redis

from hiretrack_common.queue.base import Message, QueueError
from hiretrack_common.queue.metrics import QUEUE_MESSAGES_DEAD_LETTERED

logger = logging.getLogger(__name__)

STREAM_MAXLEN = 100_000  # approximate cap so a stuck consumer can't fill Redis memory


class RedisStreamQueue:
    def __init__(
        self,
        client: "redis.Redis",
        stream: str,
        group: str,
        visibility_timeout_seconds: int,
        max_receives: int,
        consumer: str | None = None,
    ) -> None:
        self.name = stream
        self._redis = client  # must be created with decode_responses=True
        self._group = group
        self._dlq = f"{stream}-dlq"
        self._idle_ms = visibility_timeout_seconds * 1000
        self._max_receives = max_receives
        self._consumer = consumer or socket.gethostname()  # the pod name in Kubernetes
        self._group_ready = False

    # ---- producer ----------------------------------------------------------------------
    def publish(self, body: dict[str, Any]) -> None:
        self.publish_many([body])

    def publish_many(self, bodies: list[dict[str, Any]]) -> None:
        try:
            pipe = self._redis.pipeline()
            for body in bodies:
                pipe.xadd(self.name, {"body": json.dumps(body)}, maxlen=STREAM_MAXLEN)
            pipe.execute()
        except redis.RedisError as exc:
            raise QueueError(f"redis publish failed: {exc}") from exc

    # ---- consumer ----------------------------------------------------------------------
    def receive(self, max_messages: int = 10, wait_seconds: int = 10) -> list[Message]:
        try:
            self._ensure_group()
            # 1) Take back messages a consumer received but never acked (it crashed, or the
            #    handler failed). This is what makes delivery "at least once".
            messages = self._claim_stale(max_messages)
            if messages:
                return messages
            # 2) Otherwise wait for new messages (">" = never delivered to this group).
            response: Any = self._redis.xreadgroup(
                self._group,
                self._consumer,
                {self.name: ">"},
                count=max_messages,
                block=wait_seconds * 1000,
            )
        except redis.RedisError as exc:
            raise QueueError(f"redis receive failed: {exc}") from exc
        return [
            self._to_message(entry_id, fields, receive_count=1)
            for _, entries in response or []
            for entry_id, fields in entries
        ]

    def ack(self, message: Message) -> None:
        try:
            pipe = self._redis.pipeline()
            pipe.xack(self.name, self._group, message.receipt)
            pipe.xdel(self.name, message.receipt)
            pipe.execute()
        except redis.RedisError as exc:
            raise QueueError(f"redis ack failed: {exc}") from exc

    def ping(self) -> None:
        try:
            self._redis.ping()
        except redis.RedisError as exc:
            raise QueueError(f"redis unreachable: {exc}") from exc

    # ---- internals ---------------------------------------------------------------------
    def _ensure_group(self) -> None:
        if self._group_ready:
            return
        try:
            # id="0": also deliver entries added before the group existed. mkstream: create
            # the stream if the producer hasn't written yet.
            self._redis.xgroup_create(self.name, self._group, id="0", mkstream=True)
        except redis.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):  # BUSYGROUP = the group already exists, fine
                raise
        self._group_ready = True

    def _claim_stale(self, count: int) -> list[Message]:
        result: Any = self._redis.xautoclaim(
            self.name, self._group, self._consumer, min_idle_time=self._idle_ms, count=count
        )
        claimed = result[1]
        messages: list[Message] = []
        for entry_id, fields in claimed:
            if not fields:  # the entry was deleted while it was pending
                continue
            deliveries = self._delivery_count(entry_id)
            if deliveries > self._max_receives:
                self._dead_letter(entry_id, fields, deliveries)
                continue
            messages.append(self._to_message(entry_id, fields, receive_count=deliveries))
        return messages

    def _delivery_count(self, entry_id: str) -> int:
        pending: Any = self._redis.xpending_range(
            self.name, self._group, min=entry_id, max=entry_id, count=1
        )
        return int(pending[0]["times_delivered"]) if pending else 1

    def _dead_letter(self, entry_id: str, fields: dict[str, str], deliveries: int) -> None:
        dead: dict[Any, Any] = {**fields, "original_id": entry_id, "deliveries": deliveries}
        pipe = self._redis.pipeline()
        pipe.xadd(self._dlq, dead)
        pipe.xack(self.name, self._group, entry_id)
        pipe.xdel(self.name, entry_id)
        pipe.execute()
        QUEUE_MESSAGES_DEAD_LETTERED.labels(self.name).inc()
        logger.error(
            "message moved to dead-letter queue",
            extra={"queue": self.name, "message_id": entry_id, "deliveries": deliveries},
        )

    @staticmethod
    def _to_message(entry_id: str, fields: dict[str, str], receive_count: int) -> Message:
        return Message(
            id=entry_id,
            body=json.loads(fields["body"]),
            receive_count=receive_count,
            receipt=entry_id,
        )
