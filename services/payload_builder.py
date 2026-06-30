from typing import Any, Dict
from datetime import datetime, timezone


class PayloadBuilder:
    """
    Transforms parsed GitHub events into the payload format
    expected by the AWS DevOps Agent.
    """

    @staticmethod
    def build_aws_payload(parsed_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wraps a parsed GitHub event into a standardized payload
        for the AWS DevOps Agent webhook.
        """
        return {
            "source": "github-agent",
            "event_type": parsed_event.get("event"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "repository": parsed_event.get("repository"),
                "branch": parsed_event.get("branch"),
                "commit_id": parsed_event.get("commit_id"),
                "author": parsed_event.get("pusher"),
                "commit_message": parsed_event.get("commit_message"),
                "original_timestamp": parsed_event.get("timestamp"),
            }
        }
