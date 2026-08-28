import unittest
import tempfile
import shutil
import asyncio
from pathlib import Path
from app.agents.coding.agent import CodingAgent
from app.budget.manager import BudgetManager

class TestTaskLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_coding_agent_execution_and_packaging(self):
        agent = CodingAgent()
        budget = BudgetManager()

        progress_events = []
        async def on_progress(text, pct):
            progress_events.append((text, pct))

        async def run_agent():
            return await agent.execute_task(
                task_id="task_lifecycle_001",
                prompt="Build me a modern SaaS dashboard with authentication",
                workspace_path=str(self.workspace),
                client=None,
                model="gpt-4o",
                budget_manager=budget,
                progress_callback=on_progress
            )

        result = asyncio.run(run_agent())
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "COMPLETED")
        self.assertGreater(len(result["files_changed"]), 0)
        self.assertTrue(Path(result["deliverable_zip"]).exists())
        self.assertGreater(result["zip_size_bytes"], 0)
        self.assertGreater(len(progress_events), 0)

if __name__ == "__main__":
    unittest.main()
