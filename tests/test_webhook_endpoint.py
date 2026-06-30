"""Integration tests for the webhook endpoint."""
import hashlib
import hmac
import json

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from app import app


@pytest.fixture
def sample_push_payload():
    return {
        "ref": "refs/heads/main",
        "after": "abc123",
        "repository": {"full_name": "user/repo"},
        "pusher": {"name": "dev"},
        "head_commit": {
            "timestamp": "2026-01-01T00:00:00Z",
            "message": "test commit"
        }
    }


def sign_payload(payload_bytes: bytes, secret: str) -> str:
    """Generate GitHub webhook signature."""
    return "sha256=" + hmac.HMAC(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()


class TestWebhookEndpoint:
    """Integration tests for POST /github/webhook."""

    @pytest.mark.asyncio
    async def test_rejects_unsigned_request(self, sample_push_payload):
        """Should return 401 when webhook secret is set but no signature."""
        with patch("routes.github.settings") as mock_settings:
            mock_settings.GITHUB_WEBHOOK_SECRET = "test-secret"

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/github/webhook",
                    json=sample_push_payload,
                    headers={"X-GitHub-Event": "push"}
                )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_accepts_valid_signed_request(self, sample_push_payload):
        """Should return 200 with valid signature."""
        secret = "test-secret"
        body = json.dumps(sample_push_payload).encode("utf-8")
        signature = sign_payload(body, secret)

        with patch("routes.github.settings") as mock_route_settings, \
             patch("services.validator.settings") as mock_validator_settings, \
             patch("webhook_handler.AWSClient.send_event", new_callable=AsyncMock) as mock_aws:
            mock_route_settings.GITHUB_WEBHOOK_SECRET = secret
            mock_validator_settings.GITHUB_WEBHOOK_SECRET = secret
            mock_aws.return_value = {"status": "skipped", "reason": "test"}

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/github/webhook",
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-GitHub-Event": "push",
                        "X-GitHub-Delivery": "test-123",
                        "X-Hub-Signature-256": signature
                    }
                )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["event_type"] == "push"

    @pytest.mark.asyncio
    async def test_skips_validation_when_no_secret(self, sample_push_payload):
        """Should skip signature check when no secret configured."""
        with patch("routes.github.settings") as mock_settings, \
             patch("webhook_handler.AWSClient.send_event", new_callable=AsyncMock) as mock_aws:
            mock_settings.GITHUB_WEBHOOK_SECRET = ""
            mock_aws.return_value = {"status": "skipped", "reason": "test"}

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/github/webhook",
                    json=sample_push_payload,
                    headers={"X-GitHub-Event": "push"}
                )

            assert response.status_code == 200
