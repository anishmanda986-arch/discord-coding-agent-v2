import time
import uuid
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field, asdict

@dataclass
class AgentMessage:
    task_id: str
    project_id: str
    source_agent: str
    target_agent: str
    type: str  # "task", "result", "event"
    priority: str = "normal"  # "low", "normal", "high"
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: str(time.time()))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AgentRouter:
    """
    Central Message Router for the Multi-Agent Architecture.
    Prevents fragile direct-mesh couplings by routing structured task messages
    between Gateway, Coding Agent, Research Agent, Testing Agent, Design Agent,
    Manager Agent, and Connector Agent.
    """

    def __init__(self):
        # agent_name -> message handler callback
        self._handlers: Dict[str, Callable[[AgentMessage], Awaitable[AgentMessage]]] = {}
        self._message_history: list = []

    def register_agent(self, agent_name: str, handler: Callable[[AgentMessage], Awaitable[AgentMessage]]) -> None:
        self._handlers[agent_name] = handler

    async def route_message(self, message: AgentMessage) -> AgentMessage:
        """
        Routes a structured message to the target agent handler.
        """
        self._message_history.append(message.to_dict())
        if len(self._message_history) > 200:
            self._message_history.pop(0)

        target = message.target_agent
        if target not in self._handlers:
            return AgentMessage(
                task_id=message.task_id,
                project_id=message.project_id,
                source_agent="router",
                target_agent=message.source_agent,
                type="result",
                priority="high",
                payload={"error": f"Target agent '{target}' is not registered with Agent Router."},
                correlation_id=message.correlation_id
            )

        handler = self._handlers[target]
        try:
            response = await handler(message)
            return response
        except Exception as e:
            return AgentMessage(
                task_id=message.task_id,
                project_id=message.project_id,
                source_agent="router",
                target_agent=message.source_agent,
                type="result",
                priority="high",
                payload={"error": f"Agent '{target}' handler execution failed: {str(e)}"},
                correlation_id=message.correlation_id
            )
