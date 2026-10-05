"""Domain errors raised by services, and the handlers that turn them into HTTP responses.

Services never import FastAPI; they raise these, and only this module knows status codes.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from hiretrack_common.domain.enums import ApplicationStatus
from hiretrack_common.logging import request_id_var

logger = logging.getLogger(__name__)


class DomainError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    status_code = 409
    code = "conflict"


class InvalidStatusTransitionError(ConflictError):
    code = "invalid_status_transition"

    def __init__(self, current: ApplicationStatus, target: ApplicationStatus) -> None:
        super().__init__(f"Cannot move an application from {current} to {target}")
        self.current = current
        self.target = target


class InvalidInputError(DomainError):
    status_code = 422
    code = "invalid_input"


class AuthenticationError(DomainError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(DomainError):
    status_code = 403
    code = "forbidden"


def error_body(code: str, message: str) -> dict[str, dict[str, str | None]]:
    return {"error": {"code": code, "message": message, "request_id": request_id_var.get()}}


async def _handle_domain_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):  # registered for DomainError only
        raise exc
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, AuthenticationError) else None
    return JSONResponse(
        status_code=exc.status_code, content=error_body(exc.code, exc.message), headers=headers
    )


async def _handle_integrity_error(_: Request, exc: Exception) -> JSONResponse:
    # Services check uniqueness first, but two concurrent requests can both pass the check;
    # the database constraint is the real guard, and the loser gets 409 instead of 500.
    logger.warning("integrity error", extra={"error": str(getattr(exc, "orig", exc))})
    return JSONResponse(
        status_code=409, content=error_body("conflict", "Conflicts with existing data")
    )


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error", extra={"path": request.url.path})
    return JSONResponse(status_code=500, content=error_body("internal_error", "Internal error"))


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _handle_domain_error)
    app.add_exception_handler(IntegrityError, _handle_integrity_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
