from typing import Dict, Any, List
from ..base import BaseAgent
from ...router.router import AgentMessage
from ...router.complexity import TaskComplexityRouter

class ManagerAgent(BaseAgent):
    """
    Manager & Coordinator Agent.
    Evaluates task complexity, decomposes multi-stage workflows, and verifies deliverable completeness.
    """

    def __init__(self):
        super().__init__(name="manager_agent", role="Workflow Coordinator & Evaluator")

    async def handle_message(self, message: AgentMessage) -> AgentMessage:
        prompt = message.payload.get("prompt", "")
        file_count = message.payload.get("file_count", 0)

        complexity, budget = TaskComplexityRouter.classify_prompt(prompt, file_count)

        decision = {
            "complexity": complexity,
            "recommended_budget": budget,
            "workflow_steps": [
                "1. Repository inspection",
                "2. Context retrieval",
                "3. Implementation pass",
                "4. Sandbox verification",
                "5. Packaging deliverable"
            ]
        }
        return self.create_result_message(message, decision)
