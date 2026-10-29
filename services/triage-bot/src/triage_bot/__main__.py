"""Entry point: `python -m triage_bot` (what the container runs)."""

import uvicorn

from triage_bot.core.config import TriageSettings
from triage_bot.main import create_app


def main() -> None:
    settings = TriageSettings()  # secrets (WEBHOOK_TOKEN, GITHUB_TOKEN) come from the environment
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        log_config=None,  # keep our JSON logging
        access_log=False,
        timeout_graceful_shutdown=20,
    )


if __name__ == "__main__":
    main()
