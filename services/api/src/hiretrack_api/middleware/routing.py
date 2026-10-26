"""Find the route *template* for a request ("/api/v1/applications/{application_id}").

Metrics are labelled with the template, never the raw path, so each ID doesn't
create a new Prometheus time series (high cardinality kills Prometheus).

The templates come from the app's OpenAPI schema (its "paths" keys are exactly the full
templates), compiled to regexes once. That is public, stable API, unlike walking FastAPI's
internal router tree, and it works before routing too (fault injection answers early).
"""

import re

from starlette.requests import Request

OPS_PATHS = frozenset({"/healthz", "/readyz", "/metrics"})
UNMATCHED = "unmatched"

type Patterns = list[tuple[re.Pattern[str], str]]


def route_template(request: Request) -> str:
    path = request.scope["path"]
    if path in OPS_PATHS:
        return str(path)
    for pattern, template in _patterns(request):
        if pattern.match(path):
            return template
    return UNMATCHED  # 404s: never label with the raw path


def _patterns(request: Request) -> Patterns:
    state = request.app.state
    patterns: Patterns | None = getattr(state, "route_patterns", None)
    if patterns is None:
        templates = request.app.openapi().get("paths", {})
        compiled = [(_compile(template), template) for template in templates]
        # Static paths before parameterised ones: /applications/export.csv must not be
        # read as /applications/{application_id}.
        compiled.sort(key=lambda item: (item[1].count("{"), -len(item[1])))
        state.route_patterns = patterns = compiled
    return patterns


def _compile(template: str) -> re.Pattern[str]:
    # "/a/{id}" -> ^/a/[^/]+$   (each {param} matches exactly one path segment)
    return re.compile("^" + re.sub(r"\\\{[^}]+\\\}", "[^/]+", re.escape(template)) + "$")
