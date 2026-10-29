from typing import Literal

from pydantic import Field, model_validator

from hiretrack_common.config import BaseServiceSettings


class QueueSettings(BaseServiceSettings):
    queue_backend: Literal["redis", "sqs"] = "redis"
    queue_name: str = "hiretrack-jobs"  # Redis stream name (SQS uses SQS_QUEUE_URL instead)

    # Redis Streams (local / docker-compose)
    redis_url: str = "redis://localhost:6379/0"
    redis_consumer_group: str = "match-scorer"

    # SQS (cloud). Credentials come from the default AWS chain (EKS Pod Identity), never keys.
    # The dead-letter queue is configured on the SQS queue itself (redrive policy, in Terraform).
    sqs_queue_url: str | None = None
    aws_region: str | None = None

    # A message not acked within this many seconds is delivered again (SQS VisibilityTimeout,
    # Redis XAUTOCLAIM min-idle). Must be longer than the slowest message takes to process.
    queue_visibility_timeout_seconds: int = Field(default=60, ge=1, le=43200)
    # After this many failed deliveries a message goes to the dead-letter queue.
    # Redis: done in code. SQS: set the same number as maxReceiveCount in the redrive policy.
    queue_max_receives: int = Field(default=5, ge=1)

    @model_validator(mode="after")
    def _sqs_needs_url(self) -> "QueueSettings":
        if self.queue_backend == "sqs" and not self.sqs_queue_url:
            raise ValueError("SQS_QUEUE_URL is required when QUEUE_BACKEND=sqs")
        return self
