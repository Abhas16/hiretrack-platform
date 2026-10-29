import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from triage_bot.clients import ClientError
from triage_bot.core.security import WebhookAuth
from triage_bot.metrics import ERRORS
from triage_bot.schemas.alertmanager import AlertmanagerWebhook, TriageResponse
from triage_bot.services.triage_service import TriageService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhooks"])


def get_service(request: Request) -> TriageService:
    service: TriageService = request.app.state.triage_service
    return service


@router.post("/webhooks/alertmanager")
def alertmanager_webhook(
    payload: AlertmanagerWebhook,
    _: WebhookAuth,
    service: Annotated[TriageService, Depends(get_service)],
) -> TriageResponse:
    try:
        return TriageResponse(results=service.handle(payload))
    except ClientError as exc:
        # 5xx makes Alertmanager retry the notification later; duplicates are prevented
        # by the fingerprint check, so retrying is safe.
        ERRORS.labels("github").inc()
        logger.error("could not file the incident", extra={"error": str(exc)})
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Issue tracker unavailable") from exc
