#!/usr/bin/env bash
# Cut the app off from PostgreSQL with a NetworkPolicy (egress only to DNS and HTTPS).
# Expected:
#   - API /readyz fails -> pods leave the load balancer -> ApiNoReadyPods (critical)
#   - liveness keeps passing (it never touches the DB), so pods are NOT restarted
#   - match-scorer /readyz fails, messages are retried (not lost)
#   - triage-bot's issue says "database" as the probable cause
# Usage: scripts/chaos/block-db-egress.sh on|off
# (Needs a CNI that enforces NetworkPolicy, e.g. VPC CNI with network policy enabled.)
source "$(dirname "$0")/lib.sh"
need kubectl

case "${1:-}" in
  on)
    log "blocking egress to anything but DNS (53) and HTTPS (443) for api + match-scorer"
    kubectl -n "$NAMESPACE" apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: chaos-block-db-egress
  labels: { chaos: "true" }
spec:
  podSelector:
    matchExpressions:
      - { key: app, operator: In, values: ["api", "match-scorer"] }
  policyTypes: ["Egress"]
  egress:
    - ports:
        - { protocol: UDP, port: 53 }
        - { protocol: TCP, port: 53 }
        - { protocol: TCP, port: 443 }
EOF
    log "undo with: $0 off"
    ;;
  off)
    kubectl -n "$NAMESPACE" delete networkpolicy chaos-block-db-egress --ignore-not-found
    log "egress restored; readiness should recover within ~10s"
    ;;
  *) die "usage: $0 on|off" ;;
esac
