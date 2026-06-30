from typing import Any, Dict, Optional


class GitHubEventParser:
    """
    Parses GitHub webhook payloads into a clean internal structure.
    Supports: push, pull_request, workflow_run, release, deployment, issues
    """

    @staticmethod
    def parse(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes to the correct parser based on the GitHub event type.
        Falls back to a generic parser for unsupported events.
        """
        parsers = {
            "push": GitHubEventParser.parse_push_event,
            "pull_request": GitHubEventParser.parse_pull_request_event,
            "workflow_run": GitHubEventParser.parse_workflow_run_event,
            "release": GitHubEventParser.parse_release_event,
            "deployment": GitHubEventParser.parse_deployment_event,
            "issues": GitHubEventParser.parse_issues_event,
        }

        parser = parsers.get(event_type, GitHubEventParser.parse_generic_event)
        return parser(payload)

    @staticmethod
    def parse_push_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event": "push",
            "repository": payload.get("repository", {}).get("full_name"),
            "branch": payload.get("ref", "").replace("refs/heads/", ""),
            "commit_id": payload.get("after"),
            "pusher": payload.get("pusher", {}).get("name"),
            "timestamp": payload.get("head_commit", {}).get("timestamp"),
            "commit_message": payload.get("head_commit", {}).get("message"),
        }

    @staticmethod
    def parse_pull_request_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        pr = payload.get("pull_request", {})
        return {
            "event": "pull_request",
            "action": payload.get("action"),
            "repository": payload.get("repository", {}).get("full_name"),
            "pr_number": pr.get("number"),
            "title": pr.get("title"),
            "author": pr.get("user", {}).get("login"),
            "source_branch": pr.get("head", {}).get("ref"),
            "target_branch": pr.get("base", {}).get("ref"),
            "state": pr.get("state"),
            "merged": pr.get("merged", False),
            "commit_id": pr.get("head", {}).get("sha"),
            "timestamp": pr.get("updated_at"),
        }

    @staticmethod
    def parse_workflow_run_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        workflow_run = payload.get("workflow_run", {})
        return {
            "event": "workflow_run",
            "action": payload.get("action"),
            "repository": payload.get("repository", {}).get("full_name"),
            "workflow_name": workflow_run.get("name"),
            "workflow_id": workflow_run.get("id"),
            "status": workflow_run.get("status"),
            "conclusion": workflow_run.get("conclusion"),
            "branch": workflow_run.get("head_branch"),
            "commit_id": workflow_run.get("head_sha"),
            "actor": workflow_run.get("actor", {}).get("login"),
            "timestamp": workflow_run.get("updated_at"),
        }

    @staticmethod
    def parse_release_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        release = payload.get("release", {})
        return {
            "event": "release",
            "action": payload.get("action"),
            "repository": payload.get("repository", {}).get("full_name"),
            "tag_name": release.get("tag_name"),
            "release_name": release.get("name"),
            "author": release.get("author", {}).get("login"),
            "prerelease": release.get("prerelease", False),
            "draft": release.get("draft", False),
            "timestamp": release.get("published_at"),
        }

    @staticmethod
    def parse_deployment_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        deployment = payload.get("deployment", {})
        return {
            "event": "deployment",
            "action": payload.get("action"),
            "repository": payload.get("repository", {}).get("full_name"),
            "environment": deployment.get("environment"),
            "ref": deployment.get("ref"),
            "commit_id": deployment.get("sha"),
            "creator": deployment.get("creator", {}).get("login"),
            "description": deployment.get("description"),
            "timestamp": deployment.get("created_at"),
        }

    @staticmethod
    def parse_issues_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        issue = payload.get("issue", {})
        return {
            "event": "issues",
            "action": payload.get("action"),
            "repository": payload.get("repository", {}).get("full_name"),
            "issue_number": issue.get("number"),
            "title": issue.get("title"),
            "author": issue.get("user", {}).get("login"),
            "state": issue.get("state"),
            "labels": [label.get("name") for label in issue.get("labels", [])],
            "timestamp": issue.get("updated_at"),
        }

    @staticmethod
    def parse_generic_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for unsupported event types."""
        return {
            "event": "unknown",
            "repository": payload.get("repository", {}).get("full_name"),
            "action": payload.get("action"),
            "sender": payload.get("sender", {}).get("login"),
        }
