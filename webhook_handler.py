from typing import Any, Dict

from logger import logger
from services.payload_builder import PayloadBuilder
from aws_client import AWSClient
from github_client import GitHubClient


class WebhookHandler:
    """
    Orchestrates webhook processing based on event type.
    Routes different events to appropriate actions.
    """

    @staticmethod
    async def handle(event_type: str, parsed_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes the parsed event to the appropriate handler.
        Returns a result dict with actions taken.
        """
        handlers = {
            "push": WebhookHandler._handle_push,
            "pull_request": WebhookHandler._handle_pull_request,
            "issues": WebhookHandler._handle_issues,
            "workflow_run": WebhookHandler._handle_workflow_run,
            "release": WebhookHandler._handle_release,
            "deployment": WebhookHandler._handle_deployment,
        }

        handler = handlers.get(event_type, WebhookHandler._handle_generic)
        return await handler(parsed_event)

    @staticmethod
    async def _handle_push(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle push events — forward to AWS for deployment pipeline."""
        logger.info(
            f"Push to {event.get('repository')}:{event.get('branch')} "
            f"by {event.get('pusher')} — {event.get('commit_message')}"
        )

        # Build and forward to AWS
        aws_payload = PayloadBuilder.build_aws_payload(event)
        aws_response = await AWSClient.send_event(aws_payload)

        return {
            "action": "forwarded_to_aws",
            "aws_delivery": aws_response
        }

    @staticmethod
    async def _handle_pull_request(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request events based on action type."""
        action = event.get("action")
        repo = event.get("repository")
        pr_number = event.get("pr_number")

        if action == "opened":
            logger.info(
                f"PR #{pr_number} opened in {repo}: {event.get('title')} "
                f"by {event.get('author')}"
            )

            # Post a commit status indicating the agent is aware
            commit_sha = event.get("commit_id")
            if commit_sha and repo:
                await GitHubClient.create_commit_status(
                    repo=repo,
                    commit_sha=commit_sha,
                    state="pending",
                    description="GitHub Agent: Processing PR",
                    context="github-agent/review"
                )

            return {"action": "pr_acknowledged", "pr_number": pr_number}

        elif action == "closed" and event.get("merged"):
            logger.info(f"PR #{pr_number} merged in {repo} — triggering deployment")

            # Forward merged PRs to AWS for deployment
            aws_payload = PayloadBuilder.build_aws_payload(event)
            aws_response = await AWSClient.send_event(aws_payload)

            return {
                "action": "pr_merged_forwarded_to_aws",
                "pr_number": pr_number,
                "aws_delivery": aws_response
            }

        else:
            logger.info(f"PR #{pr_number} {action} in {repo}")
            return {"action": f"pr_{action}", "pr_number": pr_number}

    @staticmethod
    async def _handle_issues(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue events."""
        action = event.get("action")
        repo = event.get("repository")
        issue_number = event.get("issue_number")

        logger.info(
            f"Issue #{issue_number} {action} in {repo}: {event.get('title')}"
        )

        return {
            "action": f"issue_{action}",
            "issue_number": issue_number
        }

    @staticmethod
    async def _handle_workflow_run(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow run events — forward failures to AWS."""
        action = event.get("action")
        conclusion = event.get("conclusion")
        workflow_name = event.get("workflow_name")

        logger.info(
            f"Workflow '{workflow_name}' {action}: conclusion={conclusion}"
        )

        # Forward failed workflows to AWS for alerting
        if conclusion == "failure":
            logger.warning(f"Workflow '{workflow_name}' FAILED — forwarding to AWS")
            aws_payload = PayloadBuilder.build_aws_payload(event)
            aws_response = await AWSClient.send_event(aws_payload)
            return {
                "action": "workflow_failure_forwarded",
                "aws_delivery": aws_response
            }

        return {"action": f"workflow_{action}", "conclusion": conclusion}

    @staticmethod
    async def _handle_release(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle release events — forward to AWS for deployment."""
        action = event.get("action")
        tag = event.get("tag_name")

        logger.info(f"Release {action}: {tag} in {event.get('repository')}")

        if action == "published":
            aws_payload = PayloadBuilder.build_aws_payload(event)
            aws_response = await AWSClient.send_event(aws_payload)
            return {
                "action": "release_forwarded_to_aws",
                "tag": tag,
                "aws_delivery": aws_response
            }

        return {"action": f"release_{action}", "tag": tag}

    @staticmethod
    async def _handle_deployment(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deployment events — forward to AWS."""
        logger.info(
            f"Deployment to {event.get('environment')} "
            f"in {event.get('repository')}"
        )

        aws_payload = PayloadBuilder.build_aws_payload(event)
        aws_response = await AWSClient.send_event(aws_payload)

        return {
            "action": "deployment_forwarded_to_aws",
            "environment": event.get("environment"),
            "aws_delivery": aws_response
        }

    @staticmethod
    async def _handle_generic(event: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback handler for unsupported events."""
        logger.info(f"Unhandled event type: {event.get('event')}")
        return {"action": "logged_only", "event": event.get("event")}
