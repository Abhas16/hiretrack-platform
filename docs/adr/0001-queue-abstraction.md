# ADR 0001: One queue interface, Redis Streams locally and SQS in AWS

**Status:** accepted

## Context
job-scout hands job IDs to match-scorer. In AWS the natural choice is SQS (managed, a DLQ
built in, KEDA can scale on its depth). Locally, and in CI, we don't want an AWS account or
LocalStack just to run the stack.

## Decision
A small `Queue` protocol in `libs/hiretrack_common/queue` (`publish_many`, `receive`, `ack`,
`ping`) with two backends, chosen by `QUEUE_BACKEND`:
- `redis`: Redis Streams with a consumer group. `XAUTOCLAIM` gives SQS-like redelivery after
  a visibility timeout, and the code moves a message to `<stream>-dlq` after N deliveries.
- `sqs`: boto3 with long polling. The redrive policy moves messages to the DLQ.

Both are **at-least-once**, so consumers are idempotent (`UNIQUE(user_id, job_id)` + `ON
CONFLICT DO NOTHING`).

## Consequences
- The same code and tests run everywhere; only an env var changes.
- The Redis DLQ logic is ours to maintain (around 30 lines, unit-tested with fakeredis).
- We use only features both backends share (no FIFO ordering, no message groups).
