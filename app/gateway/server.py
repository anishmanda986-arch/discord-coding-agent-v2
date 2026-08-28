import os
import json
import time
from typing import Dict, Any, Optional

from .auth import GatewayAuthenticator
from ..router.router import AgentRouter, AgentMessage
from ..router.complexity import TaskComplexityRouter
from ..agents.coding.agent import CodingAgent
from ..agents.research.agent import ResearchAgent
from ..agents.testing.agent import TestingAgent
from ..agents.design.agent import DesignAgent
from ..agents.manager.agent import ManagerAgent
from ..agents.connector.agent import ConnectorAgent
from ..api_client.discovery import ModelDiscoveryService
from ..observability.metrics import metrics_collector
from ..storage.db import Database
from ..config import config

class AgentGatewayService:
    """
    Central Agent Gateway Service.
    Coordinates agents, dispatches structured task messages, and serves REST endpoints.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database(config.database_path)
        self.authenticator = GatewayAuthenticator(config.gateway_auth_secret)
        self.router = AgentRouter()
        self.discovery = ModelDiscoveryService()

        # Initialize core agents
        self.coding_agent = CodingAgent()
        self.research_agent = ResearchAgent()
        self.testing_agent = TestingAgent()
        self.design_agent = DesignAgent()
        self.manager_agent = ManagerAgent()
        self.connector_agent = ConnectorAgent(github_token=config.github_token)

        # Register agents with router
        self.router.register_agent("coding_agent", self.coding_agent.handle_message)
        self.router.register_agent("research_agent", self.research_agent.handle_message)
        self.router.register_agent("testing_agent", self.testing_agent.handle_message)
        self.router.register_agent("design_agent", self.design_agent.handle_message)
        self.router.register_agent("manager_agent", self.manager_agent.handle_message)
        self.router.register_agent("connector_agent", self.connector_agent.handle_message)

    async def handle_connect(self, agent_id: str, agent_type: str, endpoint: str) -> Dict[str, Any]:
        """Registers external agent connection with gateway."""
        return {
            "success": True,
            "agent_id": agent_id,
            "status": "REGISTERED",
            "registered_at": time.time()
        }

    async def dispatch_task(self, task_message: AgentMessage) -> AgentMessage:
        """Routes structured task message through Agent Router."""
        return await self.router.route_message(task_message)

    async def get_health_status(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "gateway": "CODING AGENT GATEWAY",
            "version": "1.0.0",
            "timestamp": time.time(),
            "registered_agents": [
                "coding_agent", "research_agent", "testing_agent",
                "design_agent", "manager_agent", "connector_agent"
            ],
            "metrics": metrics_collector.get_metrics_report()
        }
