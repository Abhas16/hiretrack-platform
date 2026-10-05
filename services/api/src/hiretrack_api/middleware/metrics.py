"""RED metrics (Rate, Errors, Duration) for every HTTP request.

These feed the SLO: availability = non-5xx / all, latency = p95 of the histogram.
"""

import time

from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from hiretrack_api.middleware.routing import route_template

HTTP_REQUESTS = Counter(
    "http_requests_total", "HTTP requests handled", ["method", "route", "status"]
)
HTTP_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "route"],
    # 0.3 s is an explicit bucket because the SLO target is p95 < 300 ms.
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5, 5.0),
)
HTTP_IN_PROGRESS = Gauge("http_requests_in_progress", "HTTP requests in flight", ["method"])


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        route = route_template(request)
        if route == "/metrics":
            return await call_next(request)

        method = request.method
        status_code = 500  # if the app raises, it ends up as a 500
        HTTP_IN_PROGRESS.labels(method).inc()
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            HTTP_DURATION.labels(method, route).observe(time.perf_counter() - start)
            HTTP_REQUESTS.labels(method, route, str(status_code)).inc()
            HTTP_IN_PROGRESS.labels(method).dec()
