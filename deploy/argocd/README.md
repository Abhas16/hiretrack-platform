# GitOps with Argo CD

```
deploy/argocd/
├── projects/hiretrack.yaml     AppProject: allowed repos + namespaces
├── root.yaml                   app of apps (the only thing applied by hand)
└── apps/
    ├── platform-monitoring.yaml   kube-prometheus-stack, Loki, Alloy, Pushgateway
    ├── platform-delivery.yaml     Argo Rollouts, metrics-server
    └── hiretrack-dev.yaml         the app chart with values-dev.yaml (+ canary on)
deploy/platform/*.values.yaml   our values for each add-on chart (pinned chart versions)
```

## Bootstrap (once per cluster)

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm upgrade --install argocd argo/argo-cd --version 10.11.1 -n argocd --create-namespace \
  -f deploy/platform/argo-cd.values.yaml

kubectl apply -f deploy/argocd/projects/hiretrack.yaml -f deploy/argocd/root.yaml

# UI: initial admin password, then port-forward
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
kubectl -n argocd port-forward svc/argocd-server 8443:80
```

Secrets the apps expect, created by External Secrets (or by hand for a first test):
`hiretrack/hiretrack-secrets` (see deploy/README.md), `monitoring/triage-bot-webhook` (key `token`),
`monitoring/grafana-admin` (keys `admin-user`, `admin-password`).

## Sync waves (order)

| Wave | Apps | Why |
|---|---|---|
| -2 | kube-prometheus-stack | owns the ServiceMonitor / PrometheusRule CRDs |
| -1 | Loki, Alloy, Pushgateway, Argo Rollouts, metrics-server | Rollout CRD, HPA metrics |
| 1 | hiretrack-dev | uses all of the above |

## Deploying a new version

CI builds and pushes the images tagged with the git SHA, then commits
`image.tag: <sha>` into `deploy/helm/hiretrack/values-dev.yaml`. Argo CD syncs:
1. the `hiretrack-migrate` hook runs `alembic upgrade head`;
2. the API Rollout sends 20% → 50% → 100% of pods to the new version, with the
   `hiretrack-api-error-rate` analysis watching the canary's 5xx ratio;
3. if the analysis fails, the Rollout aborts and returns to the stable version by itself.

Demo of the rollback: set `api.faultInjectionRate: "0.3"` in values-dev.yaml with a new tag, then
watch `kubectl argo rollouts get rollout hiretrack-api -n hiretrack --watch`.

**Rollback by Git:** `git revert` the tag-bump commit. Argo CD syncs the old version back.
