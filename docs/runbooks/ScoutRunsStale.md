# ScoutRunsStale

**What it means:** `job-scout` (CronJob, every 6 h) hasn't finished a successful run for 13 hours.

```bash
kubectl -n hiretrack get cronjob hiretrack-job-scout      # SUSPEND? LAST SCHEDULE?
kubectl -n hiretrack get jobs --sort-by=.metadata.creationTimestamp | tail -3
kubectl -n hiretrack logs job/<latest-job>
```

| Log says | Meaning | Fix |
|---|---|---|
| `source failed` for one company | its board slug changed (HTTP 404) | update `config/sources.yaml` |
| every source failed | no egress/DNS from the pod (NAT gateway, network policy) | check egress from the namespace |
| `publishing to the queue failed` | SQS send denied or unreachable | Pod Identity role needs `sqs:SendMessage`; jobs are kept and published next run |
| robots.txt disallows | a board changed its policy | respect it: remove the source |

Run once by hand after fixing:
```bash
kubectl -n hiretrack create job --from=cronjob/hiretrack-job-scout scout-manual-$(date +%s)
```
If runs succeed but the alert stays, the Pushgateway push is failing (`pushgateway push failed` in the logs).
