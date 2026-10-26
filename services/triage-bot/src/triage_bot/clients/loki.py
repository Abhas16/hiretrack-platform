"""Loki HTTP API: https://grafana.com/docs/loki/latest/reference/loki-http-api/"""

from datetime import UTC, datetime
from typing import Any

import httpx

from triage_bot.clients import ClientError
from triage_bot.services.context import LogLine

MAX_LINE_CHARS = 400


class LokiClient:
    def __init__(self, client: httpx.Client, base_url: str) -> None:
        self._http = client
        self._base = base_url.rstrip("/")

    def recent_lines(self, logql: str, start: datetime, end: datetime, limit: int) -> list[LogLine]:
        """Newest matching lines first (direction=backward), across all streams."""
        try:
            response = self._http.get(
                f"{self._base}/loki/api/v1/query_range",
                params={
                    "query": logql,
                    "start": int(start.timestamp() * 1e9),  # Loki wants nanoseconds
                    "end": int(end.timestamp() * 1e9),
                    "limit": limit,
                    "direction": "backward",
                },
            )
            response.raise_for_status()
            body: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ClientError(f"loki: {exc}") from exc

        lines: list[LogLine] = []
        for stream in body.get("data", {}).get("result", []):
            labels = stream.get("stream", {})
            pod = labels.get("pod") or labels.get("container") or labels.get("app") or "?"
            for timestamp_ns, line in stream.get("values", []):
                lines.append(
                    LogLine(
                        timestamp=datetime.fromtimestamp(int(timestamp_ns) / 1e9, UTC),
                        pod=pod,
                        line=str(line)[:MAX_LINE_CHARS],
                    )
                )
        lines.sort(key=lambda entry: entry.timestamp, reverse=True)
        return lines[:limit]
