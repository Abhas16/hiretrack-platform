"""Application factory: wires settings, logging, middleware, routers and lifecycle."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hiretrack_api import __version__
from hiretrack_api.controllers import (
    analytics,
    applications,
    auth,
    companies,
    contacts,
    interviews,
    notes,
    ops,
    practice,
    reminders,
    resume_variants,
)
from hiretrack_api.core.config import ApiSettings, get_settings
from hiretrack_api.core.exceptions import register_exception_handlers
from hiretrack_api.interviewer.factory import build_interviewer
from hiretrack_api.middleware.fault_injection import FaultInjectionMiddleware
from hiretrack_api.middleware.metrics import PrometheusMiddleware
from hiretrack_api.middleware.request_id import HEADER as REQUEST_ID_HEADER
from hiretrack_api.middleware.request_id import RequestIdMiddleware
from hiretrack_common.db import create_db_engine, create_session_factory, ping
from hiretrack_common.logging import configure_logging

logger = logging.getLogger(__name__)


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging("api", settings.log_level, settings.log_format)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_db_engine(settings)
        app.state.session_factory = create_session_factory(engine)
        # Phase 3 adds a "queue" check here.
        app.state.readiness_checks = {"database": partial(ping, engine)}
        logger.info("api started", extra={"env": settings.app_env, "version": __version__})
        yield
        # Runs after uvicorn has finished in-flight requests (SIGTERM -> graceful shutdown).
        logger.info("api stopping")
        engine.dispose()

    app = FastAPI(
        title="HireTrack API",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env != "prod" else None,
        redoc_url=None,
    )
    app.state.settings = settings
    app.state.interviewer = build_interviewer(settings)
    register_exception_handlers(app)

    # Middleware runs outermost-last-added: CORS -> request ID -> metrics -> fault injection.
    # Metrics sit outside fault injection on purpose, so injected 500s are counted —
    # that is what the canary analysis watches.
    app.add_middleware(FaultInjectionMiddleware, rate=settings.fault_injection_rate)
    app.add_middleware(PrometheusMiddleware)
    app.add_middleware(RequestIdMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
            expose_headers=[REQUEST_ID_HEADER, "Content-Disposition"],
        )

    app.include_router(ops.router)
    api = APIRouter(prefix="/api/v1")
    for module in (
        auth,
        applications,
        interviews,
        notes,
        companies,
        contacts,
        reminders,
        resume_variants,
        analytics,
        practice,
    ):
        api.include_router(module.router)
    app.include_router(api)
    return app
