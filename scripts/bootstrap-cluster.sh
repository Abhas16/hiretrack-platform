#!/usr/bin/env bash
# One-time setup of a fresh dev cluster, AFTER `terraform apply` in infra/terraform/envs/dev:
#   1. kubeconfig for the new cluster
#   2. fill the account-specific values in deploy/helm/hiretrack/values-dev.yaml from
#      `terraform output` (commit + push them: Argo CD reads values from Git, not from disk)
#   3. install Argo CD, then the AppProject + root app; from then on Git drives the cluster
# Usage: scripts/bootstrap-cluster.sh            (from the repo root)
set -euo pipefail

TF_DIR=infra/terraform/envs/dev
VALUES=deploy/helm/hiretrack/values-dev.yaml
ARGOCD_CHART_VERSION=10.11.1

log() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
need() { command -v "$1" >/dev/null || { echo "missing tool: $1" >&2; exit 1; }; }
for tool in terraform aws kubectl helm sed; do need "$tool"; done
tf_out() { terraform -chdir="$TF_DIR" output -raw "$1"; }

log "reading terraform outputs"
REGION=$(tf_out region)
CLUSTER=$(tf_out cluster_name)
REGISTRY=$(tf_out ecr_registry)
DB_HOST=$(tf_out rds_endpoint)
QUEUE_URL=$(tf_out sqs_queue_url)
ROLE_ARN=$(tf_out github_actions_role_arn)

log "kubeconfig for $CLUSTER"
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER"
kubectl get nodes -o wide

log "writing account-specific values into $VALUES"
# Each sed edits the first line with that key (they appear once in the file).
sed -i -E "s|^  registry: .*|  registry: ${REGISTRY}|" "$VALUES"
sed -i -E "s|^  DB_HOST: .*|  DB_HOST: ${DB_HOST}|" "$VALUES"
sed -i -E "s|^  SQS_QUEUE_URL: .*|  SQS_QUEUE_URL: ${QUEUE_URL}|" "$VALUES"
sed -i -E "s|^  AWS_REGION: .*|  AWS_REGION: ${REGION}|" "$VALUES"
git --no-pager diff --stat -- "$VALUES" || true

log "installing Argo CD $ARGOCD_CHART_VERSION"
helm repo add argo https://argoproj.github.io/argo-helm >/dev/null 2>&1 || true
helm repo update argo >/dev/null
helm upgrade --install argocd argo/argo-cd --version "$ARGOCD_CHART_VERSION" \
  -n argocd --create-namespace -f deploy/platform/argo-cd.values.yaml --wait --timeout 10m

log "AppProject + app of apps"
kubectl apply -f deploy/argocd/projects/hiretrack.yaml -f deploy/argocd/root.yaml

cat <<MSG

Done. Still to do (once):
  1. Commit and push $VALUES to main (Argo CD deploys what is in Git).
  2. GitHub repo -> Settings -> Secrets and variables -> Actions -> Variables:
       AWS_ROLE_ARN   = ${ROLE_ARN}
       DEPLOY_ENABLED = true      (set it to false again before scripts/teardown.sh)
     Then run the "release" workflow (Actions tab) to build + push the first images.
  3. Watch:  kubectl -n argocd get applications -w
     App URL: kubectl -n hiretrack get ingress hiretrack -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
     Argo CD: kubectl -n argocd port-forward svc/argocd-server 8443:80   (user admin)
              kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
MSG
