# ApiNoReadyPods

**What it means:** no API pod passes its readiness probe, so the load balancer has nothing to send traffic to.
The site is down.

```bash
kubectl -n hiretrack get pods -l app=api
kubectl -n hiretrack describe pod <pod>        # Events: probe failures, image pull, OOMKilled
kubectl -n hiretrack logs <pod> --previous     # if it is restarting
```

1. **Pods running but not ready** → `/readyz` checks the database:
   ```bash
   kubectl -n hiretrack exec <pod> -- python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/readyz').read())"
   ```
   `"database": "failed"` → RDS status in the console, the security group from the node/pod to RDS on 5432,
   and the `DB_PASSWORD` in the Secret (`kubectl -n hiretrack get externalsecret`, then check that it's synced).
2. **CrashLoopBackOff** → settings validation fails at start-up (missing `JWT_SECRET`, short secret,
   bad `DB_SSLMODE`). The error is in `logs --previous`.
3. **ImagePullBackOff** → wrong tag, or the node role can't pull from ECR.
4. **Pending** → no capacity: `kubectl get nodeclaims` (Karpenter) and the pod's Events.
