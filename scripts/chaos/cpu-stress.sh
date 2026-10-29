#!/usr/bin/env bash
# Burn CPU inside every API pod for N seconds. Expected: CPU above the HPA target -> the HPA
# adds replicas (and Karpenter adds a node if they don't fit); latency may rise
# (ApiLatencyP95High). After it ends, the HPA scales back down after its 5-minute window.
# Usage: scripts/chaos/cpu-stress.sh [seconds]   (default 300)
source "$(dirname "$0")/lib.sh"
need kubectl

SECONDS_TO_BURN="${1:-300}"
for POD in $(kubectl -n "$NAMESPACE" get pods -l app=api -o jsonpath='{.items[*].metadata.name}'); do
  log "stressing $POD for ${SECONDS_TO_BURN}s (2 busy processes)"
  # Plain Python: the image has no stress tool, and nothing is installed into the pod.
  kubectl -n "$NAMESPACE" exec "$POD" -- python -c "
import multiprocessing, time
def burn(end):
    while time.time() < end: pass
end = time.time() + $SECONDS_TO_BURN
ps = [multiprocessing.Process(target=burn, args=(end,)) for _ in range(2)]
[p.start() for p in ps]; [p.join() for p in ps]" &
done
log "watch: kubectl -n $NAMESPACE get hpa hiretrack-api -w"
wait
