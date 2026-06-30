import hashlib
import hmac
from fastapi import Request, HTTPException

from config import settings


class WebhookValidator:
    """
    Validates GitHub webhook signatures using HMAC SHA-256.
    Ensures incoming requests genuinely came from GitHub.
    """

    @staticmethod
    async def validate_signature(request: Request) -> bytes:
        """
        Validates the X-Hub-Signature-256 header against the request body.

        Returns the raw body bytes if valid.
        Raises HTTPException 401 if invalid or missing.
        """
        signature_header = request.headers.get("X-Hub-Signature-256")

        if not signature_header:
            raise HTTPException(
                status_code=401,
                detail="Missing X-Hub-Signature-256 header"
            )

        body = await request.body()

        secret = settings.GITHUB_WEBHOOK_SECRET.encode("utf-8")
        expected_signature = "sha256=" + hmac.HMAC(
            key=secret,
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, signature_header):
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            )

        return body
