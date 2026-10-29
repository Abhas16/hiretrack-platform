#!/usr/bin/env bash
# Send messages match-scorer can never process. Expected: the worker does NOT crash; each
# message is retried QUEUE_MAX_RECEIVES (5) times, then moved to the dead-letter queue;
# ScorerMessagesFailing fires.
#
# Usage: scripts/chaos/poison-message.sh sqs <queue-url>     (cloud: needs the AWS CLI)
#        scripts/chaos/poison-message.sh redis                (local: docker compose stack)
source "$(dirname "$0")/lib.sh"

POISON=('not json at all' '{"job_id": "not-a-uuid"}' '{"something": "else"}')

case "${1:-}" in
  sqs)
    need aws
    QUEUE_URL="${2:?usage: poison-message.sh sqs <queue-url>}"
    for body in "${POISON[@]}"; do
      aws sqs send-message --queue-url "$QUEUE_URL" --message-body "$body" --output text --query MessageId
    done
    log "after ~5 x visibility timeout, check the DLQ: aws sqs get-queue-attributes --queue-url <dlq-url> --attribute-names ApproximateNumberOfMessages"
    ;;
  redis)
    need docker
    for body in "${POISON[@]}"; do
      docker compose exec -T redis redis-cli XADD hiretrack-jobs '*' body "$body"
    done
    log "after ~5 minutes: docker compose exec redis redis-cli XLEN hiretrack-jobs-dlq"
    ;;
  *) die "usage: $0 sqs <queue-url> | redis" ;;
esac
