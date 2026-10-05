"""Prometheus helpers shared by services."""

from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, CollectorRegistry, generate_latest


def render_metrics(registry: CollectorRegistry = REGISTRY) -> tuple[bytes, str]:
    """Return the text exposition format and its content type, for a /metrics endpoint."""
    return generate_latest(registry), CONTENT_TYPE_LATEST
