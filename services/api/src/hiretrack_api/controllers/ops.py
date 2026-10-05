"""Operational endpoints for Kubernetes and Prometheus. No auth, not under /api/v1.

/healthz  liveness:  "is the process alive?"  Never touches the DB — if it did, a DB blip
                     would make Kubernetes restart every pod at once.
/readyz   readiness: "can I take traffic?"    Checks dependencies; failing just removes the
                     pod from the Service/ALB until it recovers.
/metrics  Prometheus scrape target.
"""

import logging
from collections.abc import Callable

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from hiretrack_common.metrics import render_metrics

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ops"])

type ReadinessCheck = Callable[[], None]  # raises if the dependency isn't usable


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
def readyz(request: Request) -> JSONResponse:
    checks: dict[str, ReadinessCheck] = request.app.state.readiness_checks
    results: dict[str, str] = {}
    for name, check in checks.items():
        try:
            check()
            results[name] = "ok"
        except Exception as exc:
            logger.warning("readiness check failed", extra={"check": name, "error": str(exc)})
            results[name] = "failed"
    ready = all(result == "ok" for result in results.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready", "checks": results},
    )


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)
