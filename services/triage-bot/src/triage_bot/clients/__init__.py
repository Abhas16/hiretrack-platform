"""Adapters for external systems (the "repositories" of this service)."""


class ClientError(Exception):
    """An upstream (Prometheus, Loki, GitHub) failed or answered something unexpected."""
