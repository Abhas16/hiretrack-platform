# ApiErrorBudgetFastBurn / ApiErrorBudgetSlowBurn

**What it means:** the share of `/api/*` requests answered with 5xx is burning the 99.5%
availability budget too fast. Fast burn (14.4x, 1h + 5m windows) pages; slow burn (6x, 6h +
30m) is a ticket. triage-bot has opened a GitHub issue with the error logs and the probable cause.

## 1. Was anything just deployed? (most common cause)

```bash
kubectl -n hiretrack rollout history deployment/hiretrack-api
kubectl -n hiretrack get pods -l app=api -o wide          # new pods? restarts?
```
If the errors started with a rollout, **roll back first, debug later**:
```bash
kubectl -n hiretrack rollout undo deployment/hiretrack-api   # or revert the Git commit (Argo CD)
```

## 2. Is it a chaos experiment?
Logs say `fault injected`, so `FAULT_INJECTION_RATE` is set:
```bash
kubectl -n hiretrack get deploy hiretrack-api -o jsonpath='{.spec.template.spec.containers[0].env}' | grep -i fault
```

## 3. Which route fails, and why?
Grafana → *HireTrack overview* → "Requests per second by status", then Loki:
```logql
{namespace="hiretrack", app="api"} | json | level="ERROR"
```
- `OperationalError` / `could not connect` → the database: see [ApiNoReadyPods](ApiNoReadyPods.md) step 2.
- `integrity error` (409s) is not a 5xx and never burns the budget.

## 4. After it's fixed
Write down in the issue: cause, impact (minutes, % of requests), fix, and one prevention item.
