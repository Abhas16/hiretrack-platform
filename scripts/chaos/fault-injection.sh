#!/usr/bin/env bash
# Make the API fail a share of /api/* requests with 500s (FAULT_INJECTION_RATE).
# Expected: ApiErrorBudgetFastBurn fires -> Alertmanager -> triage-bot opens a GitHub issue
# whose probable cause is "chaos-experiment" (it finds "fault injected" in the logs).
#
# Usage: scripts/chaos/fault-injection.sh 0.3     start (30% of requests fail)
#        scripts/chaos/fault-injection.sh 0       stop
#
# Note: with Argo CD self-heal on, a change made with kubectl is DRIFT and gets reverted to
# what Git says within a few minutes. That is GitOps working. For a longer experiment, or the
# canary-abort demo, set api.faultInjectionRate in values-dev.yaml and push instead.
source "$(dirname "$0")/lib.sh"
need kubectl

RATE="${1:?usage: fault-injection.sh <rate 0..1>}"
WORKLOAD=$(api_workload)
log "setting FAULT_INJECTION_RATE=$RATE on $WORKLOAD"
kubectl -n "$NAMESPACE" set env "$WORKLOAD" "FAULT_INJECTION_RATE=$RATE"
log "watch: Grafana 'HireTrack overview' -> 'Error ratio (5m) vs SLO'; alerts after ~2-5 minutes"
