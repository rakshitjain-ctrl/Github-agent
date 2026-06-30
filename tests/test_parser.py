"""Tests for GitHubEventParser."""
import pytest
from services.parser import GitHubEventParser


class TestParsePushEvent:
    """Tests for push event parsing."""

    def test_parses_basic_push(self):
        payload = {
            "ref": "refs/heads/main",
            "after": "abc123",
            "repository": {"full_name": "user/repo"},
            "pusher": {"name": "testuser"},
            "head_commit": {
                "timestamp": "2026-01-01T00:00:00Z",
                "message": "fix bug"
            }
        }
        result = GitHubEventParser.parse("push", payload)

        assert result["event"] == "push"
        assert result["repository"] == "user/repo"
        assert result["branch"] == "main"
        assert result["commit_id"] == "abc123"
        assert result["pusher"] == "testuser"
        assert result["timestamp"] == "2026-01-01T00:00:00Z"
        assert result["commit_message"] == "fix bug"

    def test_strips_refs_heads_prefix(self):
        payload = {
            "ref": "refs/heads/feature/new-thing",
            "after": "def456",
            "repository": {"full_name": "user/repo"},
            "pusher": {"name": "dev"},
            "head_commit": {"timestamp": None, "message": None}
        }
        result = GitHubEventParser.parse("push", payload)
        assert result["branch"] == "feature/new-thing"

    def test_handles_missing_fields(self):
        payload = {}
        result = GitHubEventParser.parse("push", payload)

        assert result["event"] == "push"
        assert result["repository"] is None
        assert result["branch"] == ""
        assert result["commit_id"] is None
        assert result["pusher"] is None


class TestParsePullRequestEvent:
    """Tests for pull request event parsing."""

    def test_parses_pr_opened(self):
        payload = {
            "action": "opened",
            "repository": {"full_name": "user/repo"},
            "pull_request": {
                "number": 42,
                "title": "Add feature",
                "user": {"login": "dev"},
                "head": {"ref": "feature-branch", "sha": "sha123"},
                "base": {"ref": "main"},
                "state": "open",
                "merged": False,
                "updated_at": "2026-01-01T00:00:00Z"
            }
        }
        result = GitHubEventParser.parse("pull_request", payload)

        assert result["event"] == "pull_request"
        assert result["action"] == "opened"
        assert result["pr_number"] == 42
        assert result["title"] == "Add feature"
        assert result["author"] == "dev"
        assert result["source_branch"] == "feature-branch"
        assert result["target_branch"] == "main"
        assert result["merged"] is False
        assert result["commit_id"] == "sha123"

    def test_handles_merged_pr(self):
        payload = {
            "action": "closed",
            "repository": {"full_name": "user/repo"},
            "pull_request": {
                "number": 10,
                "title": "Merged PR",
                "user": {"login": "dev"},
                "head": {"ref": "branch", "sha": "sha456"},
                "base": {"ref": "main"},
                "state": "closed",
                "merged": True,
                "updated_at": "2026-01-01T00:00:00Z"
            }
        }
        result = GitHubEventParser.parse("pull_request", payload)
        assert result["merged"] is True
        assert result["action"] == "closed"


class TestParseIssuesEvent:
    """Tests for issues event parsing."""

    def test_parses_issue_opened(self):
        payload = {
            "action": "opened",
            "repository": {"full_name": "user/repo"},
            "issue": {
                "number": 99,
                "title": "Bug report",
                "user": {"login": "reporter"},
                "state": "open",
                "labels": [{"name": "bug"}, {"name": "urgent"}],
                "updated_at": "2026-01-01T00:00:00Z"
            }
        }
        result = GitHubEventParser.parse("issues", payload)

        assert result["event"] == "issues"
        assert result["action"] == "opened"
        assert result["issue_number"] == 99
        assert result["title"] == "Bug report"
        assert result["author"] == "reporter"
        assert result["labels"] == ["bug", "urgent"]


class TestParseWorkflowRunEvent:
    """Tests for workflow_run event parsing."""

    def test_parses_workflow_completed(self):
        payload = {
            "action": "completed",
            "repository": {"full_name": "user/repo"},
            "workflow_run": {
                "name": "CI",
                "id": 12345,
                "status": "completed",
                "conclusion": "failure",
                "head_branch": "main",
                "head_sha": "sha789",
                "actor": {"login": "dev"},
                "updated_at": "2026-01-01T00:00:00Z"
            }
        }
        result = GitHubEventParser.parse("workflow_run", payload)

        assert result["event"] == "workflow_run"
        assert result["workflow_name"] == "CI"
        assert result["conclusion"] == "failure"
        assert result["branch"] == "main"


class TestParseGenericEvent:
    """Tests for unknown/generic events."""

    def test_unknown_event_uses_generic_parser(self):
        payload = {
            "action": "something",
            "repository": {"full_name": "user/repo"},
            "sender": {"login": "bot"}
        }
        result = GitHubEventParser.parse("unknown_event", payload)

        assert result["event"] == "unknown"
        assert result["repository"] == "user/repo"
        assert result["sender"] == "bot"
