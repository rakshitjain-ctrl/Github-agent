import uuid
from typing import Any, Dict
from datetime import datetime, timezone


class PayloadBuilder:
    """
    Transforms parsed GitHub events into the payload format
    expected by AWS DevOps Agent generic webhook.

    Required format:
    {
        "eventType": "incident",
        "incidentId": "<unique-id>",
        "action": "created",
        "priority": "HIGH" | "MEDIUM" | "LOW",
        "title": "<summary>",
        "description": "<details>",
        "timestamp": "<ISO timestamp>",
        "service": "<service name>",
        "data": { <original event data> }
    }
    """

    @staticmethod
    def build_aws_payload(parsed_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts a parsed GitHub event into the AWS DevOps Agent
        incident payload format.
        """
        event_type = parsed_event.get("event", "unknown")
        repo = parsed_event.get("repository", "unknown")
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        # Generate title and description based on event type
        title, description, priority = PayloadBuilder._build_event_details(
            event_type, parsed_event
        )

        return {
            "eventType": "incident",
            "incidentId": f"github-{event_type}-{uuid.uuid4().hex[:12]}",
            "action": "created",
            "priority": priority,
            "title": title,
            "description": description,
            "timestamp": timestamp,
            "service": repo,
            "data": {
                "metadata": {
                    "source": "github-agent",
                    "github_event_type": event_type
                },
                "github_event": parsed_event
            }
        }

    @staticmethod
    def _build_event_details(event_type: str, event: Dict[str, Any]) -> tuple:
        """Returns (title, description, priority) based on event type."""
        repo = event.get("repository", "unknown")

        if event_type == "push":
            branch = event.get("branch", "unknown")
            pusher = event.get("pusher", "unknown")
            message = event.get("commit_message", "")
            return (
                f"Push to {repo}:{branch}",
                f"Push by {pusher}: {message}",
                "MEDIUM"
            )

        elif event_type == "pull_request":
            action = event.get("action", "unknown")
            pr_number = event.get("pr_number", "?")
            title = event.get("title", "")
            return (
                f"PR #{pr_number} {action} in {repo}",
                f"Pull request: {title}",
                "HIGH" if action == "opened" else "MEDIUM"
            )

        elif event_type == "workflow_run":
            conclusion = event.get("conclusion", "unknown")
            workflow = event.get("workflow_name", "unknown")
            priority = "HIGH" if conclusion == "failure" else "LOW"
            return (
                f"Workflow '{workflow}' {conclusion} in {repo}",
                f"Workflow run completed with conclusion: {conclusion}",
                priority
            )

        elif event_type == "issues":
            action = event.get("action", "unknown")
            issue_number = event.get("issue_number", "?")
            title = event.get("title", "")
            return (
                f"Issue #{issue_number} {action} in {repo}",
                f"Issue: {title}",
                "MEDIUM"
            )

        elif event_type == "release":
            tag = event.get("tag_name", "unknown")
            return (
                f"Release {tag} published in {repo}",
                f"New release: {tag}",
                "MEDIUM"
            )

        else:
            return (
                f"GitHub event: {event_type} in {repo}",
                f"Event type: {event_type}",
                "LOW"
            )
