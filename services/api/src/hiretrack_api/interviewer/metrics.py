"""Prometheus metrics for the interviewer: how often the LLM is used, how slow it is, how often
we fall back. Useful in M8 dashboards and alerts (e.g. "LLM error rate > 20%")."""

from prometheus_client import Counter, Histogram

# operation: generate | evaluate      outcome: success | error | refusal | invalid
LLM_REQUESTS = Counter(
    "practice_llm_requests_total", "LLM calls made by the interviewer", ["operation", "outcome"]
)
LLM_DURATION = Histogram(
    "practice_llm_duration_seconds",
    "LLM call latency",
    ["operation"],
    buckets=(0.5, 1, 2, 4, 8, 15, 30, 60),
)
FALLBACKS = Counter(
    "practice_llm_fallbacks_total",
    "Times the rule-based interviewer stood in for a failed LLM call",
    ["operation"],
)
EVALUATIONS = Counter("practice_evaluations_total", "Answers evaluated", ["provider"])
