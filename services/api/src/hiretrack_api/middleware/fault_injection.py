"""Chaos testing: fail a fraction of /api/* requests with a 500 on purpose.

Set FAULT_INJECTION_RATE=0.3 on a canary and the Argo Rollouts analysis should see the
error rate jump and roll the release back. Ops endpoints are never affected, so probes
keep passing and the pod stays "healthy" while returning errors (just like a real bug).
"""

import logging
import random
from collections.abc import Callable

from prometheus_client import Counter
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from hiretrack_api.core.exceptions import error_body

logger = logging.getLogger(__name__)

FAULTS_INJECTED = Counter("fault_injections_total", "Requests failed on purpose (chaos testing)")


class FaultInjectionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, rate: float, rng: Callable[[], float] = random.random) -> None:
        super().__init__(app)
        self.rate = rate
        self.rng = rng

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self.rate > 0 and request.url.path.startswith("/api/") and self.rng() < self.rate:
            FAULTS_INJECTED.inc()
            logger.warning("fault injected", extra={"path": request.url.path})
            return JSONResponse(
                status_code=500,
                content=error_body("injected_fault", "Fault injected for chaos testing"),
            )
        return await call_next(request)
