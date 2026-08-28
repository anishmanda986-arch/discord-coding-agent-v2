import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from ..security.redaction import SecretRedactor

class GitHubClient:
    """
    GitHub REST API integration client.
    Supports repository fetching, branch creation, commit verification, and PR management.
    Ensures secrets are never exposed in commits or error logs.
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Discord-Coding-Agent",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token.strip()}"
        return headers

    async def get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        url = f"{self.base_url}/repos/{owner}/{repo}"
        headers = self._get_headers()
        loop = asyncio.get_event_loop()

        def _fetch():
            try:
                req = Request(url, headers=headers, method="GET")
                with urlopen(req, timeout=12) as response:
                    return {"success": True, "data": json.loads(response.read().decode("utf-8"))}
            except HTTPError as e:
                return {"success": False, "error": SecretRedactor.redact_text(f"GitHub HTTP {e.code}: {e.reason}")}
            except Exception as e:
                return {"success": False, "error": SecretRedactor.redact_text(str(e))}

        return await loop.run_in_executor(None, _fetch)

    async def create_pull_request(
        self, owner: str, repo: str, title: str, head: str, base: str = "main", body: str = ""
    ) -> Dict[str, Any]:
        if not self.token:
            return {"success": False, "error": "GitHub token not configured."}

        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        headers = self._get_headers()
        payload = {
            "title": SecretRedactor.redact_text(title),
            "head": head,
            "base": base,
            "body": SecretRedactor.redact_text(body or "Automated Pull Request from Coding Agent.")
        }

        loop = asyncio.get_event_loop()
        def _post():
            try:
                data = json.dumps(payload).encode("utf-8")
                req = Request(url, data=data, headers=headers, method="POST")
                with urlopen(req, timeout=15) as res:
                    return {"success": True, "pr": json.loads(res.read().decode("utf-8"))}
            except HTTPError as e:
                return {"success": False, "error": SecretRedactor.redact_text(f"GitHub PR Error {e.code}: {e.reason}")}
            except Exception as e:
                return {"success": False, "error": SecretRedactor.redact_text(str(e))}

        return await loop.run_in_executor(None, _post)
