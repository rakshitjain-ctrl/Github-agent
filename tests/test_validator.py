"""Tests for WebhookValidator."""
import hashlib
import hmac
import json

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException

from services.validator import WebhookValidator


class TestWebhookValidator:
    """Tests for webhook signature validation."""

    @pytest.mark.asyncio
    async def test_rejects_missing_signature_header(self):
        """Should raise 401 when X-Hub-Signature-256 is missing."""
        request = AsyncMock()
        request.headers = {}

        with pytest.raises(HTTPException) as exc_info:
            await WebhookValidator.validate_signature(request)

        assert exc_info.value.status_code == 401
        assert "Missing" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_rejects_invalid_signature(self):
        """Should raise 401 when signature doesn't match."""
        body = b'{"test": "data"}'
        request = AsyncMock()
        request.headers = {"X-Hub-Signature-256": "sha256=invalid"}
        request.body = AsyncMock(return_value=body)

        with patch("services.validator.settings") as mock_settings:
            mock_settings.GITHUB_WEBHOOK_SECRET = "test-secret"

            with pytest.raises(HTTPException) as exc_info:
                await WebhookValidator.validate_signature(request)

            assert exc_info.value.status_code == 401
            assert "Invalid" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_accepts_valid_signature(self):
        """Should return body when signature is valid."""
        body = b'{"test": "data"}'
        secret = "test-secret"

        # Compute correct signature
        expected_sig = "sha256=" + hmac.HMAC(
            key=secret.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        request = AsyncMock()
        request.headers = {"X-Hub-Signature-256": expected_sig}
        request.body = AsyncMock(return_value=body)

        with patch("services.validator.settings") as mock_settings:
            mock_settings.GITHUB_WEBHOOK_SECRET = secret
            result = await WebhookValidator.validate_signature(request)

        assert result == body
