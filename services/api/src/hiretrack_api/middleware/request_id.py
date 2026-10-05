"""Give every request an ID (reuse a safe incoming X-Request-ID), and write one access log line."""

import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from hiretrack_api.middleware.routing import OPS_PATHS, route_template
from hiretrack_common.logging import request_id_var

logger = logging.getLogger("hiretrack_api.access")

HEADER = "X-Request-ID"
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")  # don't echo arbitrary client input into logs


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(HEADER, "")
        request_id = incoming if _SAFE_ID.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[HEADER] = request_id
            return response
        finally:
            # Probes hit /healthz every few seconds; keep them out of INFO logs.
            level = logging.DEBUG if request.url.path in OPS_PATHS else logging.INFO
            logger.log(
                level,
                "request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "route": route_template(request),
                    "status": status_code,
                    "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                },
            )
            request_id_var.reset(token)
