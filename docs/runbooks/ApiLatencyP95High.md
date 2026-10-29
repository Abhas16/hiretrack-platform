# ApiLatencyP95High

**What it means:** p95 latency of `/api/*` has been above the 300 ms SLO for 10 minutes.

1. **Recent deploy?** Compare p95 before/after in Grafana ("p95 latency by route"). Roll back if it lines up.
2. **One route or all?** One route = a slow query or N+1 (relationships are `lazy="raise"`, so look
   for a new query in that repository). All routes = shared resource:
3. **Database:** RDS CPU, `DatabaseConnections`, and pool waits. Pool size per pod is
   `DB_POOL_SIZE + DB_MAX_OVERFLOW`; total = that × replicas, which must stay below `max_connections`.
4. **CPU throttling / saturation:**
   ```promql
   sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="hiretrack", container="api"}[5m]))
   ```
   If pods sit at their request, the HPA should be adding replicas. Check `kubectl -n hiretrack get hpa`.
5. **The practice interviewer with Claude** (`LLM_PROVIDER=anthropic`) adds seconds to its own routes
   only; it doesn't explain an all-route slowdown.
