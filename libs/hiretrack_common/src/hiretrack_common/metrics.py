"""Prometheus helpers shared by services."""

import logging

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    generate_latest,
    push_to_gateway,
)

logger = logging.getLogger(__name__)


def render_metrics(registry: CollectorRegistry = REGISTRY) -> tuple[bytes, str]:
    """Return the text exposition format and its content type, for a /metrics endpoint."""
    return generate_latest(registry), CONTENT_TYPE_LATEST


def push_metrics(gateway_url: str | None, job: str, registry: CollectorRegistry) -> None:
    """Push a CronJob's metrics to the Prometheus Pushgateway before the process exits.

    A CronJob pod lives for seconds, so Prometheus would almost never catch it with a scrape.
    The Pushgateway keeps the last pushed values until the next run replaces them (same `job`).
    A failed push is logged, not raised: losing one run's metrics must not fail the run itself
    (the "last success" alert will still notice if runs stop pushing).
    """
    if not gateway_url:
        return
    try:
        push_to_gateway(gateway_url, job=job, registry=registry, timeout=5)
    except Exception as exc:  # network errors, 4xx/5xx from the gateway
        logger.warning("pushgateway push failed", extra={"job": job, "error": str(exc)})
