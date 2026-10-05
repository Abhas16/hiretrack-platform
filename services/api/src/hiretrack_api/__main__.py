"""Entry point: `python -m hiretrack_api` (this is what the container should run)."""

import uvicorn

from hiretrack_api.core.config import get_settings
from hiretrack_api.main import create_app


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        log_config=None,  # keep our JSON logging
        access_log=False,  # RequestIdMiddleware writes the access log
        timeout_graceful_shutdown=settings.shutdown_grace_seconds,
    )


if __name__ == "__main__":
    main()
