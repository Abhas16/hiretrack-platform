"""Queue abstraction: Redis Streams locally, Amazon SQS in the cloud (QUEUE_BACKEND=redis|sqs).

Delivery is AT-LEAST-ONCE on both backends: a message can arrive twice (a worker crashed after
doing the work but before ack), so every consumer must be idempotent.
"""

from hiretrack_common.queue.base import Message, Queue, QueueError
from hiretrack_common.queue.factory import build_queue
from hiretrack_common.queue.settings import QueueSettings

__all__ = ["Message", "Queue", "QueueError", "QueueSettings", "build_queue"]
