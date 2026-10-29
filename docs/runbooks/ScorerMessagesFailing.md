# ScorerMessagesFailing / ScorerNotReady

**What it means:** match-scorer can't process job messages. Failed messages are retried after the
visibility timeout; after `QUEUE_MAX_RECEIVES` (5) attempts SQS moves them to the **dead-letter queue**.
Nothing is lost, but no new matches appear in the review queue.

```bash
kubectl -n hiretrack get pods -l app=match-scorer
kubectl -n hiretrack logs deploy/hiretrack-match-scorer | grep -i "processing failed" | tail
kubectl -n hiretrack exec deploy/hiretrack-match-scorer -- python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:9100/readyz').read())"
```

- `/readyz` shows `"queue": "failed"` → SQS permissions: the Pod Identity association for the
  `hiretrack-match-scorer` service account, and the role's `sqs:ReceiveMessage`/`DeleteMessage`/`GetQueueAttributes`.
- `"database": "failed"` → see [ApiNoReadyPods](ApiNoReadyPods.md) step 1.
- Both ok but every message fails → a bug or one bad job; the exception in the logs says which.

## Messages in the DLQ
```bash
aws sqs get-queue-attributes --queue-url <dlq-url> --attribute-names ApproximateNumberOfMessages
aws sqs receive-message --queue-url <dlq-url> --max-number-of-messages 1   # look, don't delete
```
After the fix, redrive the DLQ to the main queue (SQS console → *Start DLQ redrive*). Re-processing
is safe: the scorer is idempotent (`UNIQUE(user_id, job_id)`).
