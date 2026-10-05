# HireTrack API

FastAPI service for the job-search tracker: auth, applications (with a status state machine),
board, interviews, notes, contacts, reminders, resume variants, analytics and CSV export.

## Layers

```
HTTP ─▶ middleware/      request ID + access log, Prometheus metrics, fault injection
     ─▶ controllers/     routes, request validation, status codes. No DB, no rules.
     ─▶ services/        business rules + transaction boundary (commit). No FastAPI, no SQL.
     ─▶ repositories/    SQLAlchemy queries, always filtered by user_id. No rules.
     ─▶ models/          ORM tables (shared with the workers via libs/hiretrack_common)
        schemas/         Pydantic request/response DTOs
        core/            settings, DB session, security (Argon2 + JWT), domain errors → HTTP
```

Rules that keep it honest:
- Services raise domain errors (`NotFoundError`, `InvalidStatusTransitionError`, ...);
  only `core/exceptions.py` maps them to HTTP status codes.
- Other users' records return **404**, not 403, so IDs can't be probed.
- Relationships are `lazy="raise"`: a missing eager-load fails loudly instead of causing N+1 queries.

## Run locally

Prerequisites: [uv](https://docs.astral.sh/uv/), and a PostgreSQL 16 you start yourself.

```bash
cp .env.example .env               # then set DB_PASSWORD and JWT_SECRET
uv sync --all-packages             # make install
uv run alembic -c services/api/alembic.ini upgrade head          # make migrate
uv run uvicorn hiretrack_api.main:create_app --factory --reload  # make run-api
```

Open http://localhost:8000/docs, call `POST /api/v1/auth/register`, then `POST /api/v1/auth/login`,
click **Authorize** and paste the `access_token`.

In a container, run `python -m hiretrack_api` (no reload; graceful shutdown on SIGTERM).

## Tests

```bash
uv run pytest -m "not integration"   # unit tests with in-memory fakes (no Docker)
uv run pytest -m integration         # real Postgres via testcontainers (Docker running)
uv run ruff check . && uv run mypy libs/hiretrack_common/src services/api/src
```

The integration suite also asserts that **Alembic migrations exactly match the ORM models**,
so a forgotten `alembic revision --autogenerate` fails CI.

## Operations

| Endpoint | Purpose | Touches DB? |
|---|---|---|
| `GET /healthz` | liveness probe | no (a DB blip must not restart every pod) |
| `GET /readyz` | readiness probe, 503 if a dependency is down | yes |
| `GET /metrics` | Prometheus scrape | no |

Metrics: `http_requests_total{method,route,status}`, `http_request_duration_seconds` (histogram with
a 0.3 s bucket for the p95 < 300 ms SLO), `http_requests_in_progress`, `fault_injections_total`.
Labels use the route template (`/api/v1/applications/{application_id}`), never raw IDs.

Logs: one JSON object per line on stdout with `request_id`; send `X-Request-ID` to correlate.

Chaos: `FAULT_INJECTION_RATE=0.3` makes 30% of `/api/*` requests return 500 while probes stay green.

## Environment variables

See [`.env.example`](../../.env.example). Secrets: `DB_PASSWORD`, `JWT_SECRET`.
Migrations need only the `DB_*` variables (the migration Job doesn't need the JWT secret).
