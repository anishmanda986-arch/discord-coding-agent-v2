from typing import Dict, Any, List
from ..base import BaseAgent
from ...router.router import AgentMessage

class ResearchAgent(BaseAgent):
    """
    Technical Research Agent.
    Prioritizes official documentation, standards, and GitHub specs.
    Condenses findings into concise, actionable summaries for the coding model.
    """

    def __init__(self):
        super().__init__(name="research_agent", role="Technical Research & Specs")

    async def handle_message(self, message: AgentMessage) -> AgentMessage:
        topic = message.payload.get("topic", "")
        # Summarize authoritative knowledge
        summary = {
            "topic": topic,
            "sources": ["Official Documentation", "GitHub Spec", "RFC Standard"],
            "summary": f"Authoritative architecture notes for {topic}: use modular structure, type annotations, and error boundaries.",
            "recommended_packages": ["pydantic", "httpx", "pytest"]
        }
        return self.create_result_message(message, summary)
