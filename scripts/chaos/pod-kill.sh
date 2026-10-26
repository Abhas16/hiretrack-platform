#!/usr/bin/env bash
# Kill one API pod while traffic flows. Expected: ZERO failed requests, because
#   - 2+ replicas behind the Service, the PDB keeps one running,
#   - the readiness probe removes the dying pod from the endpoints, preStop delays shutdown,
#   - uvicorn finishes in-flight requests on SIGTERM.
# Usage: APP_URL=https://<host> scripts/chaos/pod-kill.sh [app-label]   (default: api)
source "$(dirname "$0")/lib.sh"
need kubectl

APP="${1:-api}"
POD=$(kubectl -n "$NAMESPACE" get pods -l "app=$APP" -o jsonpath='{.items[0].metadata.name}')
[[ -n "$POD" ]] || die "no pod with app=$APP in $NAMESPACE"

traffic_loop 30 &
LOOP=$!
sleep 5
log "deleting $POD (graceful: SIGTERM, then the grace period)"
kubectl -n "$NAMESPACE" delete pod "$POD" --wait=false
wait "$LOOP"
kubectl -n "$NAMESPACE" get pods -l "app=$APP"
