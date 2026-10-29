from hiretrack_common.queue.base import Queue
from hiretrack_common.queue.settings import QueueSettings


def build_queue(settings: QueueSettings) -> Queue:
    """Pick the backend from QUEUE_BACKEND. Imports are local, so a service only loads the
    library of the backend it actually uses."""
    if settings.queue_backend == "sqs":
        import boto3

        from hiretrack_common.queue.sqs import SqsQueue

        queue_url = settings.sqs_queue_url or ""  # never empty: QueueSettings validates it
        client = boto3.client("sqs", region_name=settings.aws_region)
        return SqsQueue(client, queue_url, settings.queue_visibility_timeout_seconds)

    import redis

    from hiretrack_common.queue.redis_streams import RedisStreamQueue

    client = redis.Redis.from_url(
        settings.redis_url, decode_responses=True, socket_timeout=30, socket_connect_timeout=5
    )
    return RedisStreamQueue(
        client,
        stream=settings.queue_name,
        group=settings.redis_consumer_group,
        visibility_timeout_seconds=settings.queue_visibility_timeout_seconds,
        max_receives=settings.queue_max_receives,
    )
