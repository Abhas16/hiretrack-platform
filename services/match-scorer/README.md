# match-scorer

A long-running **queue worker** (Deployment, scaled by KEDA on queue depth). For each job ID it
receives, it scores the job 0-100 against every active match profile, picks the best resume
variant, writes an application kit, and stores a match for the review queue.

```
queue ─▶ consumers/JobConsumer ─▶ services/MatchService ─▶ scoring.score_job()  (pure)
 (SQS or     receive / ack /          load job + profiles      resume_picker.pick_variant()
  Redis)     retry / drop bad         release DB connection     kit writer (template | Claude)
                                      insert ON CONFLICT DO NOTHING ─▶ matches table
```

## Score (0-100)

| Part | Points | How |
|---|---|---|
| Skills | 60 | your weight of matched skills ÷ (matched + the job's skills you lack, by taxonomy weight) |
| Role | 20 | best word overlap of the job title with one of your target roles ("site reliability" = "sre") |
| Location | 10 | remote (if you accept remote) or one of your locations |
| Experience | 10 | the advert's highest "N+ years" minimum vs your years (one year short = half points) |

Gaps list the missing skills (heaviest first), an `N+ years experience (you have M)` line and a
location mismatch, so the UI can show *why* a score is low. Skills come from `config/skills.yaml`
(aliases such as `k8s` → kubernetes, matched as whole words).

## At-least-once delivery, made safe

| Situation | What happens |
|---|---|
| Success | message acked (deleted) |
| Handler raises (DB down, bug) | not acked → visible again after `QUEUE_VISIBILITY_TIMEOUT_SECONDS` → retried; after `QUEUE_MAX_RECEIVES` it goes to the dead-letter queue |
| Malformed message | acked + logged (retrying can't fix it) |
| Same job delivered twice | profiles that already have a match are skipped, and `UNIQUE(user_id, job_id)` + `ON CONFLICT DO NOTHING` covers two workers racing |
| SIGTERM (scale-down, rollout) | finishes the current message, stops receiving, exits |

## Ops endpoints (port `OPS_PORT`, default 9100)

- `/healthz`: heartbeat-based. It fails if the loop hasn't ticked for `HEARTBEAT_MAX_AGE_SECONDS`,
  so a stuck worker is restarted.
- `/readyz`: checks the database and the queue.
- `/metrics`: `scorer_jobs_processed_total{outcome}`, `scorer_processing_seconds`,
  `matches_created_total`, `queue_messages_failed_total{queue}`,
  `queue_messages_dead_lettered_total{queue}` (Redis only), and `scorer_kit_llm_requests_total{outcome}`.

## Kit writer

`LLM_PROVIDER=none` (default): templates filled from the matched skills (free, deterministic).
`LLM_PROVIDER=anthropic`: Claude writes it with a JSON schema. On any error or refusal it falls
back to the template, so scoring never stops because of the LLM. The job advert is passed as
untrusted data, and the prompt says never to follow instructions inside it.

## Run locally

```bash
make run-scorer          # = uv run python -m match_scorer   (Ctrl+C = graceful stop)
curl localhost:9100/readyz
```

## Tests

`uv run pytest services/match-scorer` (pure scoring, kit, service with fakes, consumer loop).
The end-to-end flow on a real Postgres is in `services/api/tests/integration/test_smart_apply_flow.py`.
