#!/usr/bin/env bash
# Shared helpers for the chaos scripts. Sourced, not run.
set -euo pipefail

NAMESPACE="${NAMESPACE:-hiretrack}"
APP_URL="${APP_URL:-}"   # e.g. https://hiretrack.example.com (for the traffic loop)

log() { printf '\033[1;34m[chaos]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[chaos]\033[0m %s\n' "$*" >&2; exit 1; }

need() { command -v "$1" >/dev/null || die "needs '$1' on PATH"; }

# API workload: a Rollout when the canary is enabled, otherwise a Deployment.
api_workload() {
  if kubectl -n "$NAMESPACE" get rollout hiretrack-api >/dev/null 2>&1; then
    echo "rollout/hiretrack-api"
  else
    echo "deployment/hiretrack-api"
  fi
}

# Sends one request per 0.2 s for N seconds and counts non-2xx answers, so you can see
# whether the "chaos" was visible to users.
traffic_loop() {
  local seconds="$1" ok=0 failed=0 end=$((SECONDS + $1))
  [[ -n "$APP_URL" ]] || { log "APP_URL not set, skipping the traffic loop"; return 0; }
  log "sending traffic to $APP_URL/readyz for ${seconds}s"
  while (( SECONDS < end )); do
    if curl -fsS -o /dev/null --max-time 2 "$APP_URL/readyz"; then ok=$((ok + 1)); else failed=$((failed + 1)); fi
    sleep 0.2
  done
  log "requests ok=$ok failed=$failed"
}
