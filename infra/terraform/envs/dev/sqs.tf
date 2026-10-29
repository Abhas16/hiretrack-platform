# Smart Apply queue: job-scout publishes new job IDs, match-scorer consumes them.
# A message received 5 times without being deleted (the scorer kept failing) moves to the DLQ,
# so one poison message can't block the queue or retry forever.

resource "aws_sqs_queue" "jobs_dlq" {
  name                      = "${local.name}-jobs-dlq"
  message_retention_seconds = 1209600 # 14 days (the maximum) to inspect and redrive
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue" "jobs" {
  name = "${local.name}-jobs"

  # Must match QUEUE_VISIBILITY_TIMEOUT_SECONDS in the chart: how long a received message
  # stays hidden from other consumers before it is redelivered.
  visibility_timeout_seconds = 60
  message_retention_seconds  = 345600 # 4 days
  receive_wait_time_seconds  = 10     # default long polling (the app also asks for it)
  sqs_managed_sse_enabled    = true   # encrypted at rest with an SQS-owned key

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.jobs_dlq.arn
    maxReceiveCount     = 5 # = QUEUE_MAX_RECEIVES in the chart
  })
}

# Only the main queue may use this DLQ as its dead-letter target.
resource "aws_sqs_queue_redrive_allow_policy" "jobs_dlq" {
  queue_url = aws_sqs_queue.jobs_dlq.id
  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.jobs.arn]
  })
}
