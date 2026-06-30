"""Tests for PayloadBuilder."""
import pytest
from services.payload_builder import PayloadBuilder


class TestPayloadBuilder:
    """Tests for AWS DevOps Agent payload building."""

    def test_builds_push_payload(self):
        parsed_event = {
            "event": "push",
            "repository": "user/repo",
            "branch": "main",
            "commit_id": "abc123",
            "pusher": "dev",
            "commit_message": "fix bug",
            "timestamp": "2026-01-01T00:00:00Z"
        }
        result = PayloadBuilder.build_aws_payload(parsed_event)

        assert result["eventType"] == "incident"
        assert result["action"] == "created"
        assert result["priority"] == "MEDIUM"
        assert "Push to user/repo:main" in result["title"]
        assert result["service"] == "user/repo"
        assert "incidentId" in result
        assert result["incidentId"].startswith("github-push-")

    def test_builds_pr_payload_high_priority(self):
        parsed_event = {
            "event": "pull_request",
            "action": "opened",
            "repository": "user/repo",
            "pr_number": 1,
            "title": "New feature",
        }
        result = PayloadBuilder.build_aws_payload(parsed_event)

        assert result["priority"] == "HIGH"
        assert "PR #1 opened" in result["title"]

    def test_builds_workflow_failure_high_priority(self):
        parsed_event = {
            "event": "workflow_run",
            "action": "completed",
            "repository": "user/repo",
            "workflow_name": "CI",
            "conclusion": "failure",
        }
        result = PayloadBuilder.build_aws_payload(parsed_event)

        assert result["priority"] == "HIGH"
        assert "CI" in result["title"]
        assert "failure" in result["title"]

    def test_payload_has_required_fields(self):
        """AWS DevOps Agent requires specific fields."""
        parsed_event = {
            "event": "push",
            "repository": "user/repo",
            "branch": "main",
        }
        result = PayloadBuilder.build_aws_payload(parsed_event)

        # All required fields per AWS schema
        assert "eventType" in result
        assert "incidentId" in result
        assert "action" in result
        assert "priority" in result
        assert "title" in result
        assert result["eventType"] == "incident"
        assert result["action"] in ["created", "updated", "closed", "resolved"]
        assert result["priority"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"]

    def test_includes_original_event_in_data(self):
        parsed_event = {
            "event": "issues",
            "repository": "user/repo",
            "issue_number": 5,
            "title": "Bug",
            "action": "opened",
        }
        result = PayloadBuilder.build_aws_payload(parsed_event)

        assert "data" in result
        assert result["data"]["github_event"] == parsed_event
