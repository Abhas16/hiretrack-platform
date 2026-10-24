from prometheus_client import Counter

# Every failed attempt (the message will be retried, or dead-lettered once out of attempts).
QUEUE_MESSAGES_FAILED = Counter(
    "queue_messages_failed_total", "Queue messages whose processing failed", ["queue"]
)
# Only the Redis backend moves messages to the DLQ itself; with SQS, AWS does it (watch the
# DLQ's ApproximateNumberOfMessagesVisible in CloudWatch instead).
QUEUE_MESSAGES_DEAD_LETTERED = Counter(
    "queue_messages_dead_lettered_total", "Messages moved to the dead-letter queue", ["queue"]
)
