"""Amazon SQS backend (boto3).

Credentials: boto3's default chain. In EKS that is Pod Identity (the agent hands the pod
temporary credentials for its service account's IAM role), so there are no access keys anywhere.
Local testing against LocalStack: set AWS_ENDPOINT_URL; boto3 reads it by itself.
The dead-letter queue is AWS's job: the queue's redrive policy moves a message there after
maxReceiveCount receives without a delete.
"""

import json
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from hiretrack_common.queue.base import Message, QueueError, parse_body

SQS_MAX_BATCH = 10  # SendMessageBatch / ReceiveMessage limit
SQS_MAX_WAIT = 20  # long-polling limit in seconds


class SqsQueue:
    def __init__(self, client: Any, queue_url: str, visibility_timeout_seconds: int) -> None:
        self.name = queue_url.rsplit("/", 1)[-1]
        self._sqs = client
        self._url = queue_url
        self._visibility = visibility_timeout_seconds

    def publish(self, body: dict[str, Any]) -> None:
        self.publish_many([body])

    def publish_many(self, bodies: list[dict[str, Any]]) -> None:
        for start in range(0, len(bodies), SQS_MAX_BATCH):
            chunk = bodies[start : start + SQS_MAX_BATCH]
            entries = [
                {"Id": str(i), "MessageBody": json.dumps(body)} for i, body in enumerate(chunk)
            ]
            try:
                response = self._sqs.send_message_batch(QueueUrl=self._url, Entries=entries)
            except (BotoCoreError, ClientError) as exc:
                raise QueueError(f"sqs publish failed: {exc}") from exc
            # A batch call can partly fail; treat that as a failure so the caller notices.
            if response.get("Failed"):
                raise QueueError(f"sqs rejected {len(response['Failed'])} messages")

    def receive(self, max_messages: int = 10, wait_seconds: int = 10) -> list[Message]:
        try:
            response = self._sqs.receive_message(
                QueueUrl=self._url,
                MaxNumberOfMessages=min(max_messages, SQS_MAX_BATCH),
                # Long polling: wait for messages instead of many empty (billed) calls.
                WaitTimeSeconds=min(wait_seconds, SQS_MAX_WAIT),
                VisibilityTimeout=self._visibility,
                MessageSystemAttributeNames=["ApproximateReceiveCount"],
            )
        except (BotoCoreError, ClientError) as exc:
            raise QueueError(f"sqs receive failed: {exc}") from exc
        return [
            Message(
                id=item["MessageId"],
                body=parse_body(item["Body"]),
                receive_count=int(item.get("Attributes", {}).get("ApproximateReceiveCount", 1)),
                receipt=item["ReceiptHandle"],
            )
            for item in response.get("Messages", [])
        ]

    def ack(self, message: Message) -> None:
        try:
            self._sqs.delete_message(QueueUrl=self._url, ReceiptHandle=message.receipt)
        except (BotoCoreError, ClientError) as exc:
            raise QueueError(f"sqs delete failed: {exc}") from exc

    def ping(self) -> None:
        try:
            self._sqs.get_queue_attributes(
                QueueUrl=self._url, AttributeNames=["ApproximateNumberOfMessages"]
            )
        except (BotoCoreError, ClientError) as exc:
            raise QueueError(f"sqs unreachable: {exc}") from exc
