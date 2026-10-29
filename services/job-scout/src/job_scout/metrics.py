"""Scout metrics, in their OWN registry: this is exactly what gets pushed to the Pushgateway.

Each push replaces the previous run's values (same job name), so the counters below are
"this run" numbers. scout_last_success_timestamp powers the "scout hasn't succeeded in 3h" alert.
"""

from prometheus_client import CollectorRegistry, Counter, Gauge

REGISTRY = CollectorRegistry()

JOBS_FETCHED = Counter(
    "scout_jobs_fetched_total",
    "Listings fetched from job boards (after keyword filter)",
    ["source"],
    registry=REGISTRY,
)
JOBS_NEW = Counter("scout_jobs_new_total", "Listings not seen before (stored)", registry=REGISTRY)
SOURCE_ERRORS = Counter(
    "scout_source_errors_total",
    "Companies whose board could not be read",
    ["source"],
    registry=REGISTRY,
)
JOBS_PUBLISHED = Counter(
    "scout_jobs_published_total", "Job IDs published to the queue", registry=REGISTRY
)
RUN_DURATION = Gauge("scout_run_duration_seconds", "How long the last run took", registry=REGISTRY)
LAST_SUCCESS = Gauge(
    "scout_last_success_timestamp", "Unix time of the last successful run", registry=REGISTRY
)
