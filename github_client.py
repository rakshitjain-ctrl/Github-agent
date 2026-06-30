from typing import Any, Dict, Optional

import httpx

from config import settings


class GitHubClient:
    """
    Communicates with GitHub's REST API.
    Used for posting commit statuses, comments, and fetching repo info.
    """

    BASE_URL = "https://api.github.com"

    @staticmethod
    def _get_headers() -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    @staticmethod
    async def create_commit_status(
        repo: str,
        commit_sha: str,
        state: str,
        description: Optional[str] = None,
        context: str = "github-agent"
    ) -> Dict[str, Any]:
        """
        Posts a commit status to GitHub.

        Args:
            repo: Full repo name (e.g., "rakshit/github-agent")
            commit_sha: The SHA of the commit
            state: One of "pending", "success", "failure", "error"
            description: Short status description
            context: Label for this status check
        """
        url = f"{GitHubClient.BASE_URL}/repos/{repo}/statuses/{commit_sha}"

        payload = {
            "state": state,
            "description": description or f"GitHub Agent: {state}",
            "context": context
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=GitHubClient._get_headers()
                )

            return {
                "status": "sent",
                "status_code": response.status_code,
                "response": response.json()
            }

        except httpx.RequestError as e:
            return {
                "status": "error",
                "reason": f"GitHub API request failed: {str(e)}"
            }
