import json

from fastapi import APIRouter, Request, HTTPException

from config import settings
from logger import logger
from services.parser import GitHubEventParser
from services.validator import WebhookValidator
from webhook_handler import WebhookHandler

router = APIRouter(
    prefix="/github",
    tags=["GitHub"]
)


@router.post("/webhook")
async def github_webhook(request: Request):

    # Step 1: Validate signature (if secret is configured)
    if settings.GITHUB_WEBHOOK_SECRET:
        try:
            body = await WebhookValidator.validate_signature(request)
            payload = json.loads(body)
        except HTTPException:
            logger.warning("Webhook rejected: invalid or missing signature")
            raise
    else:
        payload = await request.json()

    # Step 2: Determine event type from GitHub header
    event_type = request.headers.get("X-GitHub-Event", "push")
    delivery_id = request.headers.get("X-GitHub-Delivery", "unknown")

    logger.info(f"Received webhook: event={event_type}, delivery={delivery_id}")

    # Step 3: Parse the event
    try:
        parsed = GitHubEventParser.parse(event_type, payload)
    except Exception as e:
        logger.error(f"Failed to parse {event_type} event: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to parse event: {str(e)}")

    # Step 4: Route to appropriate handler
    try:
        result = await WebhookHandler.handle(event_type, parsed)
    except Exception as e:
        logger.error(f"Handler error for {event_type}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal processing error")

    return {
        "status": "success",
        "event_type": event_type,
        "delivery_id": delivery_id,
        "result": result
    }
