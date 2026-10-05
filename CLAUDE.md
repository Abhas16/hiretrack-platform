# Project: HireTrack — Job Search Tracker + Smart Apply, on an AWS EKS DevSecOps Platform

## About me
I'm Abhas, a junior DevOps engineer (AZ-400, AZ-104, AZ-900) with a React/TypeScript background.
This is a resume portfolio project. I must be able to EXPLAIN every line in an interview.

## Ownership — read this first
- **You (Claude) build the APPLICATION code**: services' source code, tests, app-level config,
  `.env.example`, seed data, and app READMEs.
- **I (Abhas) build ALL DevOps/infra myself** for hands-on learning: Dockerfiles, docker-compose,
  Terraform, Helm, Kubernetes manifests, GitHub Actions, Argo CD, monitoring config, scripts.
- For anything in my area, act as a **mentor**: review my files, point out bugs, security issues and
  best practices, give hints and links to docs — but do NOT write the full file unless I explicitly
  say "write it for me". When reviewing, rank issues as must-fix / should-fix / nice-to-have.
- Make the app easy to operate: every setting from env vars, health/readiness endpoints, Prometheus
  metrics, JSON logs to stdout, graceful shutdown on SIGTERM, no local-disk state.

## Must be different from my other project
My other repo (github.com/Abhas16/boutique-microservices) is an e-commerce shop on AWS EKS with
Node.js. Do not reuse its domain, UI style, service names or layout. This project is also on AWS,
so it must show the next level: Python, event-driven workers, SQS + KEDA, Pod Identity, managed
RDS, DevSecOps CI, canary releases, SLOs and incident automation.

## Cloud target (AWS)
EKS (+ Karpenter, spot), ECR, RDS PostgreSQL (private), SQS (+ dead-letter queue), SSM Parameter
Store / Secrets Manager via External Secrets Operator, EKS Pod Identity, ALB via AWS Load Balancer
Controller, S3 remote state. App code uses the default AWS credential chain (Pod Identity in the
cluster) — never access keys. `AWS_REGION` comes from env.

## The application
### 1. Tracker
- Entities: User, Company, Application (role, company, location, source, job URL, status,
  applied_at, resume_variant_id), Interview, Contact, Note, Reminder, ResumeVariant (name, tags/skills).
- Status flow: WISHLIST → APPLIED → INTERVIEW → OFFER; WISHLIST/APPLIED/INTERVIEW/OFFER → REJECTED.
  APPLIED → WISHLIST allowed. Everything else returns 409 from the service layer.
- Features: JWT auth, Kanban board, applications table with filters/search, interviews,
  analytics (per week, funnel, by source, by resume variant, avg days to first interview), CSV export.
- **reminder-worker** (CronJob): creates follow-up reminders for APPLIED with no update in 7 days.

### 2. Smart Apply (human-in-the-loop — the user always submits the application themselves)
- **job-scout** (runs as a CronJob): fetches new listings ONLY from public job-board APIs
  (Greenhouse, Lever, Ashby public board endpoints) for a list of companies in
  `config/sources.yaml`. Normalizes to a Job, de-duplicates by hash, stores new jobs, publishes job
  IDs to a queue. Respects rate limits (configurable delay, retries with backoff, timeouts), sends
  an honest User-Agent, and checks robots.txt.
- **match-scorer** (queue worker, scalable): scores each job 0–100 against the user profile
  (skills with weights, target roles, locations, max years of experience). Output: score, matched
  skills, gaps (incl. "N+ years" detection), suggested resume variant (tag overlap), and an
  application kit: short cover note + 2–3 tailored resume bullets. Kit generation is template-based
  by default; optional LLM via `LLM_PROVIDER=none|anthropic`.
- **Review queue** API + UI: list matches above a threshold; approve (creates an APPLIED application
  and returns the job URL to open), skip, view/copy kit.
- Non-goals: NO auto-submitting, NO browser automation or clicking on job portals, NO scraping
  sites whose terms forbid it, NO storing portal credentials.
- Queue abstraction: `QUEUE_BACKEND=redis|sqs` (Redis Streams locally, Amazon SQS in cloud via boto3).
  Delivery is at-least-once, so consumers must be idempotent; failed messages go to a dead-letter queue.
- CronJobs (scout, reminder-worker) exit after each run, so they push metrics to a Prometheus
  Pushgateway when `PUSHGATEWAY_URL` is set. Long-running services expose `/metrics`.
- Metrics to expose: `scout_jobs_fetched_total{source}`, `scout_jobs_new_total`,
  `scout_run_duration_seconds`, `scout_last_success_timestamp`, `scorer_jobs_processed_total`,
  `scorer_processing_seconds`, `matches_created_total`, `matches_approved_total`, `queue_messages_failed_total`.

### 3. triage-bot
Receives Alertmanager webhooks, queries Prometheus + Loki for 15 min of context, opens a GitHub
Issue (alert, affected pods, error-log excerpts, metric snapshot, probable cause, runbook link).
`LLM_PROVIDER=none` (rule-based, default) | `anthropic`.

## Backend architecture (Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2)
Strict layers in every Python service:
- `controllers/` HTTP only (routers, validation, status codes) — no DB, no business rules
- `services/` business logic · `repositories/` DB access · `models/` ORM · `schemas/` DTOs
- `core/` config, logging, security, exceptions, database · `middleware/` request ID, metrics
- Workers (scout, scorer, reminder) use the same layers with `jobs/` or `consumers/` instead of controllers.
- API under `/api/v1`; ops endpoints `/healthz`, `/readyz` (checks DB + queue), `/metrics`.
- `FAULT_INJECTION_RATE` env var on the API for chaos testing.
- Tests: pytest, unit tests with fakes, integration tests with testcontainers. ruff + mypy.

## Frontend (React 18 + TypeScript + Vite)
SaaS dashboard: dark sidebar (Dashboard, Board, Review queue, Applications, Analytics), top bar
with search + Add application, login screen, toasts showing API results. Match the demo UI in
`docs/design/`. Tailwind CSS, TanStack Query, React Router, React Hook Form + Zod, dnd-kit,
Recharts, Vitest. Runtime config via `/config.json` (API base URL) so one image works in every env.

## Repository structure
```
hiretrack-platform/
├── .github/                     (mine) workflows, templates, CODEOWNERS, dependabot.yml
├── services/
│   ├── api/                     src/hiretrack_api/{controllers,services,repositories,models,schemas,core,middleware}
│   ├── web/                     src/{app,features,components,lib,types}
│   ├── job-scout/               src/job_scout/{sources,services,repositories,core,jobs}
│   ├── match-scorer/            src/match_scorer/{consumers,services,repositories,core}
│   ├── reminder-worker/
│   └── triage-bot/
├── libs/hiretrack_common/       shared DB models, queue abstraction, logging, metrics helpers
├── config/                      sources.yaml, skills.yaml (taxonomy + weights)
├── infra/terraform/             (mine)
├── deploy/                      (mine) helm/, argocd/, platform/
├── observability/               (mine) dashboards/, rules/, alertmanager/
├── scripts/                     (mine) chaos/, teardown.sh; seed-data.py (yours)
├── docs/                        design/, adr/, runbooks/, setup/
├── Makefile                     app targets (yours): test, lint, run-*
└── README.md
```

## Rules for you (Claude)
- Work phase by phase (PROMPTS.md). STOP at the end of each phase and suggest a conventional commit.
- After each file, explain it in 2–4 lines.
- Never run cloud write commands (terraform apply/destroy, az create/delete, kubectl delete).
- No hardcoded secrets or IDs. Pin dependency versions.
