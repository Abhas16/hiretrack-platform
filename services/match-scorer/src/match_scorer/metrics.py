"""Scorer metrics (default registry, scraped from the ops server's /metrics)."""

from prometheus_client import Counter, Histogram

# outcome: ok | error (will be retried) | invalid (malformed message, dropped)
JOBS_PROCESSED = Counter(
    "scorer_jobs_processed_total", "Queue messages handled by the scorer", ["outcome"]
)
PROCESSING_SECONDS = Histogram(
    "scorer_processing_seconds",
    "Time to score one job for every profile (incl. kit generation)",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
)
MATCHES_CREATED = Counter("matches_created_total", "Matches stored for the review queue")
KIT_LLM_REQUESTS = Counter(
    "scorer_kit_llm_requests_total", "LLM calls for application kits", ["outcome"]
)
