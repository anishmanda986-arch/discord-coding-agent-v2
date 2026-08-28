import unittest
import asyncio
from app.router.complexity import TaskComplexityRouter
from app.router.router import AgentRouter, AgentMessage

class TestAgentRouterAndComplexity(unittest.TestCase):
    def test_complexity_classification(self):
        c1, b1 = TaskComplexityRouter.classify_prompt("fix typo in readme")
        self.assertEqual(c1, "TRIVIAL")
        self.assertEqual(b1["model_type"], "fast")

        c2, b2 = TaskComplexityRouter.classify_prompt("Build me a modern SaaS dashboard with authentication from scratch")
        self.assertEqual(c2, "COMPLEX")
        self.assertEqual(b2["model_type"], "strong")

        c3, b3 = TaskComplexityRouter.classify_prompt("add a simple helper function to format dates")
        self.assertEqual(c3, "SMALL")

    def test_agent_router_structured_messaging(self):
        router = AgentRouter()

        async def mock_handler(msg: AgentMessage) -> AgentMessage:
            return AgentMessage(
                task_id=msg.task_id,
                project_id=msg.project_id,
                source_agent="testing_agent",
                target_agent=msg.source_agent,
                type="result",
                payload={"status": "ok", "tests_passed": 12}
            )

        router.register_agent("testing_agent", mock_handler)

        async def send_msg():
            inbound = AgentMessage(
                task_id="t1",
                project_id="p1",
                source_agent="gateway",
                target_agent="testing_agent",
                type="task",
                payload={"action": "run_tests"}
            )
            return await router.route_message(inbound)

        resp = asyncio.run(send_msg())
        self.assertEqual(resp.source_agent, "testing_agent")
        self.assertEqual(resp.payload["status"], "ok")
        self.assertEqual(resp.payload["tests_passed"], 12)

if __name__ == "__main__":
    unittest.main()
