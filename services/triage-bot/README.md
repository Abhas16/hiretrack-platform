# triage-bot

A small FastAPI service that Alertmanager calls (webhook receiver). For each **firing** alert
it gathers the last 15 minutes of context and opens a **GitHub issue**, so whoever is on call
starts from evidence instead of a bare alert name.

```
Alertmanager ──POST /webhooks/alertmanager (Bearer token)──▶ controllers/webhooks.py
                                                                  │
   services/triage_service.py ── open issue for this fingerprint? ─┤ yes → skip (duplicate)
                                                                  │ no
   services/gatherer.py ── Prometheus: the alert's own PromQL over the window (from generatorURL)
                       ── Prometheus: pods with restarts in the namespace
                       ── Loki: latest error/warn lines for the alert's namespace/app/pod
   services/cause_rules.py (or llm_analyst.py) ── probable cause + next steps
   services/report.py ── Markdown issue ──▶ clients/github.py ──▶ GitHub Issues API
```

| Alert state | Open issue? | Action |
|---|---|---|
| firing | no | gather context, analyse, **open issue** |
| firing | yes | nothing (Alertmanager repeats every `repeat_interval`) |
| resolved | yes | **comment** "resolved", left open for the follow-up |
| resolved | no | nothing |

## Design decisions (interview talking points)

- **Every context source is optional.** If Prometheus or Loki is down (often exactly during an
  incident) the issue is still filed, with a "Missing context" section.
- **GitHub failure → HTTP 502**, so Alertmanager retries the notification. Retries are safe:
  the alert fingerprint is written in the issue body and searched before filing (plus an
  in-memory cache, because GitHub's search index lags a few seconds).
- **Untrusted text stays inert.** Label values are escaped before going into PromQL/LogQL (no
  query injection); log lines go in a code fence with fences neutralised; `@` in table cells is
  broken, so logs can't ping people.
- **Rules first, LLM optional.** `LLM_PROVIDER=none` uses ordered rules (chaos experiment,
  database, OOM, crash loop, queue/DLQ, scout, latency, error rate). With `anthropic`, Claude
  writes the analysis, and any LLM error falls back to the rules.
- **Dry run** when `GITHUB_TOKEN`/`GITHUB_REPO` are unset: issues are logged, not filed.

## Alertmanager config (for your Helm values)

```yaml
receivers:
  - name: triage-bot
    webhook_configs:
      - url: http://triage-bot.hiretrack.svc:8080/webhooks/alertmanager
        send_resolved: true
        http_config:
          authorization:
            credentials_file: /etc/alertmanager/secrets/triage-bot-token/token
```

## Metrics

`triage_alerts_total{action}`, `triage_errors_total{stage}`, `triage_processing_seconds`.

## Run / test

```bash
make run-triage
curl -X POST localhost:8080/webhooks/alertmanager -H "Authorization: Bearer $WEBHOOK_TOKEN" \
  -H "Content-Type: application/json" -d @services/triage-bot/tests/sample-alert.json
uv run pytest services/triage-bot
```
