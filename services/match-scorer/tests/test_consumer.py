import uuid
from typing import Any

from hiretrack_common.ops_server import Heartbeat
from hiretrack_common.queue import Message, QueueError
from hiretrack_common.shutdown import ShutdownSignal
from match_scorer.consumers.job_consumer import JobConsumer


class FakeQueue:
    name = "jobs"

    def __init__(self, batches: list[list[Message]], shutdown: ShutdownSignal) -> None:
        self.batches = batches
        self.shutdown = shutdown
        self.acked: list[str] = []

    def receive(self, max_messages: int = 10, wait_seconds: int = 10) -> list[Message]:
        if not self.batches:
            self.shutdown.request()  # nothing left: end the loop
            return []
        batch = self.batches.pop(0)
        if batch and batch[0].id == "boom":
            raise QueueError("connection reset")
        return batch

    def ack(self, message: Message) -> None:
        self.acked.append(message.id)

    def publish(self, body: dict[str, Any]) -> None: ...

    def publish_many(self, bodies: list[dict[str, Any]]) -> None: ...

    def ping(self) -> None: ...


def msg(message_id: str, body: dict[str, Any]) -> Message:
    return Message(id=message_id, body=body, receive_count=1, receipt=message_id)


def run(batches: list[list[Message]], handler: Any) -> FakeQueue:
    shutdown = ShutdownSignal()
    queue = FakeQueue(batches, shutdown)
    JobConsumer(queue, handler, shutdown, Heartbeat(60), sleep=lambda _: None).run()
    return queue


def test_success_is_acked_and_failure_is_not() -> None:
    ok_id, bad_id = uuid.uuid4(), uuid.uuid4()

    def handler(job_id: uuid.UUID) -> int:
        if job_id == bad_id:
            raise RuntimeError("db down")
        return 1

    queue = run([[msg("a", {"job_id": str(ok_id)}), msg("b", {"job_id": str(bad_id)})]], handler)
    assert queue.acked == ["a"]  # "b" stays unacked -> redelivered later -> DLQ eventually


def test_malformed_messages_are_left_for_the_dlq() -> None:
    bad = [
        msg("x", {"nope": 1}),
        msg("y", {"job_id": "not-a-uuid"}),
        msg("z", {"_unparseable": "<html>"}),  # what the queue gives for non-JSON bodies
    ]
    queue = run([bad], lambda _: 0)
    assert queue.acked == []  # never acked -> retried -> dead-letter queue


def test_queue_errors_do_not_kill_the_worker() -> None:
    job = uuid.uuid4()
    queue = run([[msg("boom", {})], [msg("a", {"job_id": str(job)})]], lambda _: 1)
    assert queue.acked == ["a"]


def test_stops_taking_messages_after_shutdown() -> None:
    shutdown = ShutdownSignal()
    handled: list[uuid.UUID] = []

    def handler(job_id: uuid.UUID) -> int:
        handled.append(job_id)
        shutdown.request()  # SIGTERM arrives while the first message is processed
        return 1

    ids = [uuid.uuid4(), uuid.uuid4()]
    queue = FakeQueue([[msg(str(i), {"job_id": str(i)}) for i in ids]], shutdown)
    JobConsumer(queue, handler, shutdown, Heartbeat(60), sleep=lambda _: None).run()
    assert handled == ids[:1]  # the current message finished and was acked; the 2nd was left
    assert queue.acked == [str(ids[0])]
