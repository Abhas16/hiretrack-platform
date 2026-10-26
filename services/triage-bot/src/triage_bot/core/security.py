"""Only Alertmanager may call the webhook: it sends a shared bearer token."""

import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)


def require_webhook_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> None:
    expected: str = request.app.state.settings.webhook_token.get_secret_value()
    given = credentials.credentials if credentials else ""
    # compare_digest takes the same time however many characters match, so the token
    # can't be guessed one character at a time by measuring response times.
    if not hmac.compare_digest(given.encode(), expected.encode()):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid webhook token", {"WWW-Authenticate": "Bearer"}
        )


WebhookAuth = Annotated[None, Depends(require_webhook_token)]
