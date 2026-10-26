from prometheus_client import Counter, Histogram

# action: created | duplicate | resolved_comment | ignored
ALERTS_HANDLED = Counter("triage_alerts_total", "Alerts received from Alertmanager", ["action"])
# stage: prometheus | loki | github | analysis
ERRORS = Counter("triage_errors_total", "Failures while gathering context or filing", ["stage"])
PROCESSING_SECONDS = Histogram(
    "triage_processing_seconds",
    "Time to triage one alert (context + analysis + issue)",
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10, 30),
)
