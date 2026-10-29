# PodCrashLooping

**What it means:** a pod in the namespace restarted more than 3 times in 15 minutes.

```bash
kubectl -n hiretrack describe pod <pod>    # Last State: Terminated -> Reason + Exit Code
kubectl -n hiretrack logs <pod> --previous
```

| Reason / exit code | Usual cause |
|---|---|
| `OOMKilled` (137) | memory limit too low, or a leak. Compare `container_memory_working_set_bytes` with the limit |
| `Error` (1) at start-up | settings validation (missing/short secret, bad value). The first log lines say which |
| liveness probe failed | for match-scorer: the heartbeat went stale, so the loop is stuck (hung DB/queue call) |
| `CreateContainerConfigError` | a referenced Secret key is missing. Check the ExternalSecret sync |
