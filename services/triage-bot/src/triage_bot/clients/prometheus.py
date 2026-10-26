"""Prometheus HTTP API: https://prometheus.io/docs/prometheus/latest/querying/api/"""

from datetime import datetime
from typing import Any

import httpx

from triage_bot.clients import ClientError
from triage_bot.services.context import MetricSeries

MAX_SERIES = 10  # an issue is for humans; the full picture is one click away in Grafana


class PrometheusClient:
    def __init__(self, client: httpx.Client, base_url: str) -> None:
        self._http = client
        self._base = base_url.rstrip("/")

    def range_summary(
        self, query: str, start: datetime, end: datetime, step_seconds: int = 60
    ) -> list[MetricSeries]:
        """Run the alert's own expression over the window; summarise each series."""
        data = self._get(
            "/api/v1/query_range",
            {
                "query": query,
                "start": start.timestamp(),
                "end": end.timestamp(),
                "step": step_seconds,
            },
        )
        series: list[MetricSeries] = []
        for item in data.get("result", [])[:MAX_SERIES]:
            values = [
                float(v) for _, v in item.get("values", []) if v not in ("NaN", "+Inf", "-Inf")
            ]
            if values:
                series.append(
                    MetricSeries(item.get("metric", {}), values[-1], min(values), max(values))
                )
        return series

    def instant(self, query: str) -> list[tuple[dict[str, str], float]]:
        data = self._get("/api/v1/query", {"query": query})
        return [
            (item.get("metric", {}), float(item["value"][1]))
            for item in data.get("result", [])
            if "value" in item
        ]

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._http.get(f"{self._base}{path}", params=params)
            response.raise_for_status()
            body: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ClientError(f"prometheus: {exc}") from exc
        if body.get("status") != "success":
            raise ClientError(f"prometheus: {body.get('error', 'query failed')}")
        data: dict[str, Any] = body.get("data", {})
        return data
