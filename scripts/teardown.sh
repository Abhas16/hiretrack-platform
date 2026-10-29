#!/usr/bin/env bash
# Delete EVERYTHING for dev, in the only order that works:
#   1. the app (its Ingress -> the AWS Load Balancer Controller deletes the ALB and its SGs)
#   2. the rest of the Argo CD apps, then Argo CD itself
#   3. terraform destroy (VPC, EKS, RDS, SQS, ECR, IAM, SSM)
# If the ALB still existed at step 3, it would block deleting the subnets and the VPC.
# Usage: scripts/teardown.sh          (asks before terraform destroy)
set -euo pipefail

TF_DIR=infra/terraform/envs/dev
log() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

if kubectl get namespace argocd >/dev/null 2>&1; then
  log "deleting the app first (the Ingress owns the ALB)"
  kubectl -n argocd delete application hiretrack-dev --ignore-not-found --wait=true --timeout=10m
  kubectl -n hiretrack wait --for=delete ingress/hiretrack --timeout=5m 2>/dev/null || true

  log "waiting for the ALB to be gone"
  for _ in $(seq 1 30); do
    left=$(aws elbv2 describe-load-balancers --names hiretrack-dev --query 'length(LoadBalancers)' \
      --output text 2>/dev/null || echo 0)
    [ "$left" = "0" ] && break
    sleep 10
  done

  log "deleting the root app (and with it every platform app)"
  kubectl -n argocd delete application root --ignore-not-found --wait=true --timeout=15m

  log "uninstalling Argo CD"
  helm uninstall argocd -n argocd --wait || true
fi

log "terraform destroy ($TF_DIR)"
terraform -chdir="$TF_DIR" destroy
