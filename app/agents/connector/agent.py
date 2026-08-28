from typing import Dict, Any
from ..base import BaseAgent
from ...router.router import AgentMessage
from ...github.client import GitHubClient

class ConnectorAgent(BaseAgent):
    """
    Connector & Integrations Agent.
    Handles external connections, GitHub repository synchronizations, PR creation, and Webhooks.
    """

    def __init__(self, github_token: str = None):
        super().__init__(name="connector_agent", role="External Connectors & Integrations")
        self.github = GitHubClient(token=github_token)

    async def handle_message(self, message: AgentMessage) -> AgentMessage:
        action = message.payload.get("action", "ping")
        if action == "github_status":
            repo = message.payload.get("repo", "")
            return self.create_result_message(message, {"status": "connected", "repo": repo})
        return self.create_result_message(message, {"status": "ok", "action": action})
