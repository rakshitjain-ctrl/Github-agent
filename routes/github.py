import json

from fastapi import APIRouter, Request, HTTPException

from config import settings
from logger import logger
from services.parser import GitHubEventParser
from services.validator import WebhookValidator
from services.payload_builder import PayloadBuilder
from aws_client import AWSClient

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

    logger.info(
        f"Parsed {event_type}: repo={parsed.get('repository')}, "
        f"action={parsed.get('action', 'N/A')}"
    )

    # Step 4: Build the AWS payload
    try:
        aws_payload = PayloadBuilder.build_aws_payload(parsed)
    except Exception as e:
        logger.error(f"Failed to build AWS payload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal processing error")

    # Step 5: Forward to AWS DevOps Agent
    aws_response = await AWSClient.send_event(aws_payload)

    if aws_response["status"] == "sent":
        logger.info(f"Event forwarded to AWS: status_code={aws_response.get('status_code')}")
    elif aws_response["status"] == "skipped":
        logger.debug(f"AWS delivery skipped: {aws_response.get('reason')}")
    else:
        logger.error(f"AWS delivery failed: {aws_response.get('reason')}")

    return {
        "status": "success",
        "event_type": event_type,
        "delivery_id": delivery_id,
        "parsed_event": parsed,
        "aws_delivery": aws_response
    }
