import hashlib
import hmac
import base64
import json
from typing import Any, Dict
from datetime import datetime, timezone

import httpx

from config import settings
from logger import logger


class AWSClient:
    """
    Sends event payloads to the AWS DevOps Agent webhook.
    Uses HMAC authentication as required by AWS DevOps Agent generic webhooks.

    HMAC formula: base64(HMAC-SHA256(secret, "${timestamp}:${payload}"))
    Headers required:
      - Content-Type: application/json
      - x-amzn-event-timestamp: ISO timestamp
      - x-amzn-event-signature: base64 HMAC signature
    """

    @staticmethod
    def _generate_signature(timestamp: str, payload: str) -> str:
        """
        Generate HMAC-SHA256 signature for AWS DevOps Agent.
        Signs: "{timestamp}:{payload}" with the webhook secret.
        Returns base64-encoded signature.
        """
        secret = settings.AWS_WEBHOOK_SECRET.encode("utf-8")
        message = f"{timestamp}:{payload}".encode("utf-8")

        signature = hmac.HMAC(
            key=secret,
            msg=message,
            digestmod=hashlib.sha256
        ).digest()

        return base64.b64encode(signature).decode("utf-8")

    @staticmethod
    async def send_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends the payload to the AWS DevOps Agent webhook URL.
        Uses HMAC authentication with x-amzn-event-signature header.
        """
        if not settings.AWS_DEVOPS_WEBHOOK_URL:
            return {
                "status": "skipped",
                "reason": "AWS_DEVOPS_WEBHOOK_URL not configured"
            }

        if not settings.AWS_WEBHOOK_SECRET:
            return {
                "status": "skipped",
                "reason": "AWS_WEBHOOK_SECRET not configured"
            }

        url = settings.AWS_DEVOPS_WEBHOOK_URL
        payload_json = json.dumps(payload)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        # Generate HMAC signature
        signature = AWSClient._generate_signature(timestamp, payload_json)

        headers = {
            "Content-Type": "application/json",
            "x-amzn-event-timestamp": timestamp,
            "x-amzn-event-signature": signature
        }

        logger.info(f"Sending event to AWS: {url}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    content=payload_json.encode("utf-8"),
                    headers=headers
                )

            logger.info(f"AWS response: status_code={response.status_code}, body={response.text[:500]}")
            return {
                "status": "sent",
                "status_code": response.status_code,
                "response": response.text
            }

        except httpx.TimeoutException:
            logger.error("AWS request timed out")
            return {
                "status": "error",
                "reason": "Request to AWS DevOps Agent timed out"
            }

        except httpx.RequestError as e:
            logger.error(f"AWS request failed: {str(e)}")
            return {
                "status": "error",
                "reason": f"Request failed: {str(e)}"
            }
