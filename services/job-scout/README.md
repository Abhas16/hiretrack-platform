# job-scout

A Kubernetes **CronJob**. Each run reads the companies in `config/sources.yaml`, fetches their
open roles from the **public, documented JSON APIs** of Greenhouse, Lever and Ashby, stores the
jobs it hasn't seen before, and publishes their IDs to the queue for `match-scorer`. Then it exits.

```
sources.yaml ─▶ JobBoard adapters ─▶ keyword filter ─▶ INSERT ... ON CONFLICT DO NOTHING
 (greenhouse/      (one interface,                       (dedupe on sha256 of
  lever/ashby)      3 implementations)                    board + company + job ID)
                                                                  │ commit
                                          queue ◀─ publish jobs WHERE queued_at IS NULL
                                                   then set queued_at  (mini outbox)
```

## Layers

```
jobs/run_scout.py     entry point: wiring, exit code, Pushgateway push   (the "controller")
services/             ScoutService: the run itself, partial-failure rules, outbox publishing
sources/              one adapter per board + PoliteHttpClient (robots.txt, rate limit, retries)
repositories/         JobRepository: insert-if-new, list/mark unqueued
core/                 settings (env vars) and the sources.yaml loader
```

## Being a good citizen

- Only public board APIs that companies publish for exactly this use. No HTML scraping, no
  logins, no browser automation, and nothing is ever submitted to a job portal.
- `robots.txt` is checked per host (RFC 9309: 4xx = no rules, unreachable = disallowed).
- At most one request per `SCOUT_REQUEST_DELAY_SECONDS` per host.
- Timeouts on every request. Retries only for 429/5xx/network errors, with exponential backoff
  plus jitter, honouring `Retry-After`. A 404 (wrong slug) fails fast.
- An honest `User-Agent` naming the project (`SCOUT_USER_AGENT`).

## Failure rules (exit code)

| Situation | Result |
|---|---|
| One company's board fails (404, timeout) | logged + `scout_source_errors_total`, run continues, exit 0 |
| Every source fails | exit 1 (probably our network/DNS) |
| Queue publish fails | exit 1. Jobs stay `queued_at IS NULL`; the next run publishes them |

## Metrics (pushed to the Pushgateway when `PUSHGATEWAY_URL` is set)

`scout_jobs_fetched_total{source}`, `scout_jobs_new_total`, `scout_jobs_published_total`,
`scout_source_errors_total{source}`, `scout_run_duration_seconds`, `scout_last_success_timestamp`.
Alert idea: `time() - scout_last_success_timestamp > 3 * 3600`.

## Run locally

Needs Postgres (migrated) and Redis. Settings are in the root `.env` (see `.env.example`).

```bash
make run-scout           # = uv run python -m job_scout
```

## Tests

`uv run pytest services/job-scout`. Board responses are recorded JSON fixtures served
through `httpx.MockTransport`; tests never use the network.
