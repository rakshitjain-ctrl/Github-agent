import hashlib
import hmac
import json
from typing import Any, Dict

import httpx

from config import settings
from logger import logger


class AWSClient:
    """
    Sends event payloads to the AWS DevOps Agent webhook.
    Signs requests using HMAC SHA-256 (same pattern GitHub uses).
    """

    @staticmethod
    def _generate_signature(payload_bytes: bytes) -> str:
        """Generate HMAC SHA-256 signature for the outgoing payload."""
        return "sha256=" + hmac.HMAC(
            key=settings.AWS_WEBHOOK_SECRET.encode("utf-8"),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        ).hexdigest()

    @staticmethod
    async def send_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends the payload to the AWS DevOps Agent webhook URL.
        Returns a dict with status and response details.
        """
        if not settings.AWS_DEVOPS_WEBHOOK_URL:
            return {
                "status": "skipped",
                "reason": "AWS_DEVOPS_WEBHOOK_URL not configured"
            }

        payload_bytes = json.dumps(payload).encode("utf-8")
        signature = AWSClient._generate_signature(payload_bytes)

        headers = {
            "Content-Type": "application/json",
            "X-Signature-256": signature,
            "X-Source": "github-agent"
        }

        logger.info(f"Sending event to AWS: {settings.AWS_DEVOPS_WEBHOOK_URL}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.AWS_DEVOPS_WEBHOOK_URL,
                    content=payload_bytes,
                    headers=headers
                )

            logger.info(f"AWS response: status_code={response.status_code}")
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
