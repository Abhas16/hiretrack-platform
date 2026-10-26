# Deploying HireTrack

```
deploy/helm/hiretrack/      the app chart: api, web, migrate Job, match-scorer, 2 CronJobs,
                            triage-bot, ServiceAccounts, Ingress, NetworkPolicies,
                            ServiceMonitors, PrometheusRule (SLOs + alerts), Grafana dashboard
docker/python-service.Dockerfile   one image recipe for the 4 Python workers (SERVICE build arg)
docs/runbooks/              one page per alert (linked from each alert's runbook_url)
```

## What the AWS side must provide (the contract)

The chart contains **no AWS resources**. It expects these to exist (built with Terraform, plus
the EKS add-ons), and takes their identifiers as values:

| Need | Details | Chart value |
|---|---|---|
| **6 ECR repos** | `hiretrack-api`, `hiretrack-web`, `hiretrack-match-scorer`, `hiretrack-job-scout`, `hiretrack-reminder-worker`, `hiretrack-triage-bot` | `image.registry`, `image.tag` |
| **RDS PostgreSQL 16** | private subnets; SG allows 5432 from the cluster; DB `hiretrack`, user `hiretrack` | `config.DB_HOST` |
| **SQS queue + DLQ** | main queue `VisibilityTimeout=60`; redrive policy to the DLQ with `maxReceiveCount=5` (= `QUEUE_MAX_RECEIVES`); long polling is done by the app | `config.SQS_QUEUE_URL`, `config.AWS_REGION` |
| **Kubernetes Secret `hiretrack-secrets`** in the namespace, created by External Secrets from SSM/Secrets Manager | keys: `DB_PASSWORD`, `JWT_SECRET` (≥32 chars), `WEBHOOK_TOKEN` (≥24), optional `GITHUB_TOKEN`, `ANTHROPIC_API_KEY` | `existingSecret` |
| **Pod Identity associations** (namespace `hiretrack`) | `hiretrack-job-scout` → `sqs:SendMessage`, `sqs:GetQueueAttributes`; `hiretrack-match-scorer` → `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes`, `sqs:ChangeMessageVisibility`. Others need no AWS access | (none: matched by SA name) |
| **Ingress controller** | AWS Load Balancer Controller (`className: alb`) + ACM cert | `ingress.*` |
| **kube-prometheus-stack** in `monitoring` (+ Pushgateway, Loki) | release label `kube-prometheus-stack`; Grafana dashboard sidecar on | `monitoring.labels`, `triageBot.*Url`, `config.PUSHGATEWAY_URL` |
| Optional **KEDA** | ScaledObject on `hiretrack-match-scorer` with an `aws-sqs-queue` trigger (Pod Identity auth); then set `matchScorer.replicas: null` | `matchScorer.replicas` |

## Deploy

```bash
helm lint deploy/helm/hiretrack -f deploy/helm/hiretrack/values-dev.yaml
helm upgrade --install hiretrack deploy/helm/hiretrack -n hiretrack --create-namespace \
  -f deploy/helm/hiretrack/values-dev.yaml --set image.tag=<git sha>
```

Order of events on every install/upgrade:
1. `hiretrack-migrate` Job (pre-upgrade hook) runs `alembic upgrade head`. If it fails, nothing else changes.
2. Deployments roll (maxUnavailable 0); CronJobs pick up the new image on their next run.
3. A config change rolls the pods too (a checksum annotation of the ConfigMap).

Then seed demo data through the public URL (and DB access for Smart Apply samples):
```bash
uv run python scripts/seed-data.py --api-url https://<host>
```

## Alertmanager → triage-bot

```yaml
# kube-prometheus-stack values: alertmanager.config
route:
  receiver: triage-bot
  group_by: [alertname, namespace]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
receivers:
  - name: triage-bot
    webhook_configs:
      - url: http://hiretrack-triage-bot.hiretrack.svc:8080/webhooks/alertmanager
        send_resolved: true
        http_config:
          authorization:
            credentials_file: /etc/alertmanager/secrets/triage-bot-webhook/token
alertmanager:
  alertmanagerSpec:
    secrets: [triage-bot-webhook]   # a Secret in `monitoring` with key `token` = WEBHOOK_TOKEN
```

## Cost and teardown
`helm uninstall hiretrack -n hiretrack` deletes the Ingress, and with it the ALB. Do that
**before** `terraform destroy`, or the ALB the controller created will block deleting the VPC.
