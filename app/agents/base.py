import abc
import time
from typing import Dict, Any, Optional
from ..router.router import AgentMessage

class BaseAgent(abc.ABC):
    """
    Abstract base class for all autonomous agents in the multi-agent gateway.
    """

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    @abc.abstractmethod
    async def handle_message(self, message: AgentMessage) -> AgentMessage:
        """Processes incoming task message and returns structured result."""
        pass

    def create_result_message(
        self,
        original_message: AgentMessage,
        payload: Dict[str, Any],
        type: str = "result",
        priority: str = "normal"
    ) -> AgentMessage:
        return AgentMessage(
            task_id=original_message.task_id,
            project_id=original_message.project_id,
            source_agent=self.name,
            target_agent=original_message.source_agent,
            type=type,
            priority=priority,
            payload=payload,
            correlation_id=original_message.correlation_id,
            timestamp=str(time.time())
        )
