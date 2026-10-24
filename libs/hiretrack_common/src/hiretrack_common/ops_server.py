"""Tiny HTTP server for queue workers (no FastAPI needed): /healthz, /readyz, /metrics.

Runs in a daemon thread next to the worker loop, so Kubernetes probes and Prometheus scrapes
work the same way as for the API.

/healthz is a heartbeat check: the worker loop calls `beat()` every iteration. If the loop is
stuck (deadlock, hung network call with no timeout) the heartbeat goes stale, /healthz answers
503, and the liveness probe restarts the pod. A plain "process is up" check would miss that.
"""

import json
import logging
import threading
import time
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from hiretrack_common.metrics import render_metrics

logger = logging.getLogger(__name__)

type ReadinessCheck = Callable[[], None]  # raises if the dependency isn't usable


class Heartbeat:
    def __init__(self, max_age_seconds: float) -> None:
        self._max_age = max_age_seconds
        self._last = time.monotonic()

    def beat(self) -> None:
        self._last = time.monotonic()

    def is_fresh(self) -> bool:
        return time.monotonic() - self._last <= self._max_age


class OpsServer:
    def __init__(
        self,
        port: int,
        heartbeat: Heartbeat,
        readiness_checks: dict[str, ReadinessCheck],
        host: str = "0.0.0.0",  # noqa: S104 - probes come from the kubelet, outside the pod
    ) -> None:
        handler = _make_handler(heartbeat, readiness_checks)
        self._server = ThreadingHTTPServer((host, port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    def start(self) -> None:
        self._thread.start()
        logger.info("ops server listening", extra={"port": self.port})

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()


def _make_handler(
    heartbeat: Heartbeat, checks: dict[str, ReadinessCheck]
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # name required by BaseHTTPRequestHandler
            if self.path == "/healthz":
                fresh = heartbeat.is_fresh()
                self._json(200 if fresh else 503, {"status": "ok" if fresh else "stale"})
            elif self.path == "/readyz":
                results: dict[str, str] = {}
                for name, check in checks.items():
                    try:
                        check()
                        results[name] = "ok"
                    except Exception as exc:
                        logger.warning(
                            "readiness check failed", extra={"check": name, "error": str(exc)}
                        )
                        results[name] = "failed"
                ready = all(r == "ok" for r in results.values())
                status = "ready" if ready else "not_ready"
                self._json(200 if ready else 503, {"status": status, "checks": results})
            elif self.path == "/metrics":
                body, content_type = render_metrics()
                self._send(200, body, content_type)
            else:
                self._json(404, {"error": "not found"})

        def _json(self, status: int, payload: dict[str, object]) -> None:
            self._send(status, json.dumps(payload).encode(), "application/json")

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            pass  # probes hit this every few seconds; don't flood the logs

    return Handler
