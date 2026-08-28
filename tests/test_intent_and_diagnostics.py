import unittest
import asyncio
import tempfile
import os
import shutil
from app.router.intent import IntentRouter
from app.agents.conversation.agent import ConversationAgent
from app.api_client.diagnostics import SystemDiagnosticService
from app.tools.filesystem import FileSystemTools
from app.tools.patcher import DiffPatcher
from app.tools.safety import FileSafetyValidator, TaskBackupStore
from app.bot.commands import BotCommandsHandler
from app.storage.db import Database

class TestIntentAndDiagnostics(unittest.IsolatedAsyncioTestCase):

    async def test_intent_classification(self):
        router = IntentRouter()
        
        # Conversational prompts
        conv_prompts = [
            "hello",
            "what is React?",
            "explain recursion in simple terms",
            "who are you?",
            "how do you work?"
        ]
        for p in conv_prompts:
            intent = router.classify_intent_heuristic(p)
            self.assertEqual(intent, IntentRouter.INTENT_CONVERSATION, f"Prompt '{p}' should be classified as CONVERSATION")

        # Coding prompts
        coding_prompts = [
            "build a REST API with express",
            "create a React dashboard",
            "fix the bug in login.py",
            "refactor the database layer",
            "write unit tests for the authentication service"
        ]
        for p in coding_prompts:
            intent = router.classify_intent_heuristic(p)
            self.assertEqual(intent, IntentRouter.INTENT_CODING, f"Prompt '{p}' should be classified as CODING")

    async def test_conversation_agent_offline(self):
        agent = ConversationAgent()
        res = await agent.generate_response("hello there!")
        self.assertTrue(res["success"])
        self.assertIn("content", res)
        self.assertGreater(len(res["content"]), 0)

    async def test_system_diagnostics(self):
        service = SystemDiagnosticService()
        result = await service.run_full_system_diagnostic()
        self.assertIn("overall_status", result)
        self.assertIn("ascii_report", result)
        self.assertIn("checks", result)
        self.assertIn("latency_breakdown", result)
        self.assertGreaterEqual(len(result["checks"]), 15)

    async def test_atomic_filesystem_rollback(self):
        test_dir = tempfile.mkdtemp()
        try:
            fs = FileSystemTools(test_dir)
            # 1. Write initial file
            res1 = fs.write_file("test.py", "def add(a, b):\n    return a + b\n")
            self.assertTrue(res1["success"])

            # 2. Patch file with valid syntax
            res2 = fs.edit_file("test.py", "return a + b", "return a + b + 0")
            self.assertTrue(res2["success"])
            self.assertIn("return a + b + 0", fs.read_file("test.py")["content"])

            # 3. Attempt write with invalid Python syntax -> should trigger rollback
            res3 = fs.write_file("test.py", "def broken_syntax(:\n    return\n")
            self.assertFalse(res3["success"])
            self.assertTrue(res3.get("rolled_back", False))

            # 4. Verify previous good state is preserved
            content = fs.read_file("test.py")["content"]
            self.assertIn("return a + b + 0", content)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    async def test_bot_commands_diagnostic(self):
        test_db_file = tempfile.mktemp(suffix=".sqlite3")
        try:
            db = Database(test_db_file)
            handler = BotCommandsHandler(db)
            test_res = await handler.handle_test_command(run_full_diagnostics=True)
            self.assertTrue(test_res["success"])
            self.assertIn("ascii_report", test_res)
        finally:
            if os.path.exists(test_db_file):
                os.remove(test_db_file)

if __name__ == "__main__":
    unittest.main()
