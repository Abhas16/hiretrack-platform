# reminder-worker

A Kubernetes **CronJob** (e.g. daily at 09:00 IST). Each run creates a `FOLLOW_UP` reminder
for every **APPLIED** application that has had no status change or edit for
`FOLLOW_UP_AFTER_DAYS` (default 7), then pushes its metrics and exits.

## Safe to run twice (idempotent)

1. The query skips applications that already got a follow-up since their last status change,
   so a reminder the user dismissed isn't re-created every night.
2. The insert is `ON CONFLICT DO NOTHING` against the partial unique index
   `uq_reminders_open_follow_up` (at most one OPEN follow-up per application), so two
   overlapping runs (a retried CronJob) can't create duplicates.

Set `concurrencyPolicy: Forbid` on the CronJob anyway; the database guard is the safety net.

## Layers

```
jobs/run_reminders.py      entry point: wiring, exit code, Pushgateway push
services/                  FollowUpService: cut-off date, message text
repositories/              stale-application query + bulk insert
```

## Metrics (pushed when `PUSHGATEWAY_URL` is set)

`reminder_worker_reminders_created_total`, `reminder_worker_run_duration_seconds`,
`reminder_worker_last_success_timestamp` (alert if older than ~26 h for a daily schedule).

## Run / test

```bash
make run-reminders                       # = uv run python -m reminder_worker
uv run pytest services/reminder-worker   # unit
uv run pytest services/api/tests/integration/test_reminder_worker.py   # real Postgres
```
