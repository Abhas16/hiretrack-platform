"""Queue backends: Redis Streams against fakeredis, SQS against botocore's Stubber (no network)."""

import json
import time
import urllib.request

import boto3
import fakeredis
import pytest
from botocore.stub import Stubber
from prometheus_client import REGISTRY

from hiretrack_common.ops_server import Heartbeat, OpsServer
from hiretrack_common.queue import QueueError, QueueSettings
from hiretrack_common.queue.redis_streams import RedisStreamQueue
from hiretrack_common.queue.sqs import SqsQueue

QUEUE_URL = "https://sqs.ap-south-1.amazonaws.com/000000000000/hiretrack-jobs"


@pytest.fixture
def redis_queue() -> RedisStreamQueue:
    client = fakeredis.FakeRedis(decode_responses=True)
    return RedisStreamQueue(
        client, "jobs", "scorer", visibility_timeout_seconds=1, max_receives=2, consumer="w1"
    )


def test_redis_publish_receive_ack(redis_queue: RedisStreamQueue) -> None:
    redis_queue.publish_many([{"job_id": "a"}, {"job_id": "b"}])

    messages = redis_queue.receive(max_messages=10, wait_seconds=0)
    assert [m.body for m in messages] == [{"job_id": "a"}, {"job_id": "b"}]
    assert all(m.receive_count == 1 for m in messages)

    for message in messages:
        redis_queue.ack(message)
    time.sleep(1.1)
    assert redis_queue.receive(wait_seconds=0) == []  # acked = gone, nothing to reclaim


def test_redis_unacked_message_is_redelivered_then_dead_lettered(
    redis_queue: RedisStreamQueue,
) -> None:
    redis_queue.publish({"job_id": "poison"})
    assert redis_queue.receive(wait_seconds=0)[0].receive_count == 1  # never acked

    time.sleep(1.1)  # longer than the visibility timeout
    second = redis_queue.receive(wait_seconds=0)
    assert [m.body for m in second] == [{"job_id": "poison"}]
    assert second[0].receive_count == 2

    before = REGISTRY.get_sample_value("queue_messages_dead_lettered_total", {"queue": "jobs"})
    time.sleep(1.1)
    assert redis_queue.receive(wait_seconds=0) == []  # 3rd delivery > max_receives=2 -> DLQ
    after = REGISTRY.get_sample_value("queue_messages_dead_lettered_total", {"queue": "jobs"})
    assert (after or 0) - (before or 0) == 1

    dlq = redis_queue._redis.xrange("jobs-dlq")
    assert json.loads(dlq[0][1]["body"]) == {"job_id": "poison"}


def test_sqs_publish_batches_by_ten() -> None:
    client = boto3.client("sqs", region_name="ap-south-1")
    queue = SqsQueue(client, QUEUE_URL, visibility_timeout_seconds=60)
    with Stubber(client) as stub:
        for size in (10, 2):
            entries = [{"Id": str(i), "MessageBody": json.dumps({"n": i})} for i in range(size)]
            stub.add_response(
                "send_message_batch",
                {"Successful": [], "Failed": []},
                {"QueueUrl": QUEUE_URL, "Entries": entries},
            )
        queue.publish_many([{"n": i} for i in range(10)] + [{"n": 0}, {"n": 1}])
        stub.assert_no_pending_responses()


def test_sqs_receive_and_ack() -> None:
    client = boto3.client("sqs", region_name="ap-south-1")
    queue = SqsQueue(client, QUEUE_URL, visibility_timeout_seconds=60)
    with Stubber(client) as stub:
        stub.add_response(
            "receive_message",
            {
                "Messages": [
                    {
                        "MessageId": "m1",
                        "ReceiptHandle": "r1",
                        "Body": '{"job_id": "x"}',
                        "Attributes": {"ApproximateReceiveCount": "3"},
                    }
                ]
            },
            {
                "QueueUrl": QUEUE_URL,
                "MaxNumberOfMessages": 10,
                "WaitTimeSeconds": 20,
                "VisibilityTimeout": 60,
                "MessageSystemAttributeNames": ["ApproximateReceiveCount"],
            },
        )
        stub.add_response("delete_message", {}, {"QueueUrl": QUEUE_URL, "ReceiptHandle": "r1"})

        [message] = queue.receive(max_messages=50, wait_seconds=60)  # both get capped
        assert message.body == {"job_id": "x"}
        assert message.receive_count == 3
        queue.ack(message)


def test_sqs_errors_become_queue_errors() -> None:
    client = boto3.client("sqs", region_name="ap-south-1")
    queue = SqsQueue(client, QUEUE_URL, visibility_timeout_seconds=60)
    with Stubber(client) as stub:
        stub.add_client_error("get_queue_attributes", service_error_code="AccessDenied")
        with pytest.raises(QueueError):
            queue.ping()


def test_sqs_backend_requires_a_queue_url() -> None:
    with pytest.raises(ValueError, match="SQS_QUEUE_URL"):
        QueueSettings(queue_backend="sqs")


def test_ops_server_health_follows_the_heartbeat() -> None:
    heartbeat = Heartbeat(max_age_seconds=0.2)

    def broken() -> None:
        raise QueueError("down")

    server = OpsServer(0, heartbeat, {"queue": broken}, host="127.0.0.1")  # port 0 = any free
    server.start()
    base = f"http://127.0.0.1:{server.port}"
    try:
        with urllib.request.urlopen(f"{base}/healthz") as response:  # noqa: S310 - local test
            assert response.status == 200
        time.sleep(0.3)
        with pytest.raises(urllib.error.HTTPError) as stale:
            urllib.request.urlopen(f"{base}/healthz")  # noqa: S310
        assert stale.value.code == 503
        with pytest.raises(urllib.error.HTTPError) as not_ready:
            urllib.request.urlopen(f"{base}/readyz")  # noqa: S310
        assert json.loads(not_ready.value.read())["checks"] == {"queue": "failed"}
    finally:
        server.stop()
