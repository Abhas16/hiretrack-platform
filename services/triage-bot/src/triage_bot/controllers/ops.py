"""/healthz (liveness) and /metrics. Readiness = liveness here: the bot has no dependency it
can't work without (each context source is optional, and GitHub errors are retried)."""

from fastapi import APIRouter, Response

from hiretrack_common.metrics import render_metrics

router = APIRouter(tags=["ops"])


@router.get("/healthz")
@router.get("/readyz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)
