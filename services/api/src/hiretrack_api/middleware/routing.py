"""Find the route *template* for a request ("/api/v1/applications/{application_id}").

Metrics are labelled with the template, never the raw path, so each ID doesn't
create a new Prometheus time series (high cardinality kills Prometheus).
"""

from starlette.requests import Request
from starlette.routing import Match

OPS_PATHS = frozenset({"/healthz", "/readyz", "/metrics"})


def route_template(request: Request) -> str:
    for route in request.app.router.routes:
        match, _ = route.matches(request.scope)
        if match == Match.FULL:
            return str(getattr(route, "path", "unmatched"))
    return "unmatched"
