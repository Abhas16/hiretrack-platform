# Chaos experiments

Each experiment breaks one thing on purpose and states what *should* happen. Run it, watch
Grafana (*HireTrack overview*) and the GitHub issues, and compare with the expectation.
Anything unexpected is a finding: write it down and fix it.

| Script | Breaks | Expected result |
|---|---|---|
| `pod-kill.sh` | one API pod | 0 failed requests (PDB, readiness, preStop, graceful shutdown) |
| `fault-injection.sh 0.3` | 30% of API requests → 500 | `ApiErrorBudgetFastBurn` → triage-bot issue with cause *chaos-experiment*; with the canary, the Rollout aborts by itself |
| `cpu-stress.sh 300` | API CPU | HPA scales out (Karpenter adds a node if needed), then back in |
| `block-db-egress.sh on` | API/scorer → RDS | readiness fails, liveness doesn't (no restarts); `ApiNoReadyPods`; issue cause *database* |
| `poison-message.sh sqs <url>` | unprocessable messages | worker keeps running; 5 retries; messages in the DLQ; `ScorerMessagesFailing` |

```bash
export NAMESPACE=hiretrack APP_URL=https://<your host>
scripts/chaos/pod-kill.sh
scripts/chaos/fault-injection.sh 0.3   # ... later: scripts/chaos/fault-injection.sh 0
scripts/chaos/block-db-egress.sh on    # ... later: scripts/chaos/block-db-egress.sh off
```

Always undo each experiment before starting the next, so you know which change caused what.
