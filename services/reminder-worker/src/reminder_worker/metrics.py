"""Own registry: exactly what is pushed to the Pushgateway at the end of a run."""

from prometheus_client import CollectorRegistry, Counter, Gauge

REGISTRY = CollectorRegistry()

REMINDERS_CREATED = Counter(
    "reminder_worker_reminders_created_total", "Follow-up reminders created", registry=REGISTRY
)
RUN_DURATION = Gauge(
    "reminder_worker_run_duration_seconds", "How long the last run took", registry=REGISTRY
)
LAST_SUCCESS = Gauge(
    "reminder_worker_last_success_timestamp",
    "Unix time of the last successful run",
    registry=REGISTRY,
)
