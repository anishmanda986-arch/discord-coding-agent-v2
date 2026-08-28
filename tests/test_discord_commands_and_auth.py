import unittest
import tempfile
import shutil
import asyncio
from pathlib import Path
from app.storage.db import Database
from app.bot.commands import BotCommandsHandler
from app.bot.handlers import MessageEventHandler

class TestDiscordCommandsAndAuth(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        db_path = Path(self.tmp_dir) / "test_bot.sqlite3"
        self.db = Database(str(db_path))
        self.commands = BotCommandsHandler(self.db)
        self.handler = MessageEventHandler(self.db)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_disable_channel_isolation(self):
        async def run_test():
            # Channel 1 disabled
            res1 = await self.commands.handle_disable_command("chan_1")
            self.assertTrue(res1["is_disabled"])

            # Verify channel 1 ignores normal messages
            msg_res = await self.handler.handle_user_message(
                channel_id="chan_1",
                user_id="u1",
                content="Build an app"
            )
            self.assertEqual(msg_res, {"ignored": True, "reason": "Channel is disabled"})

            # Verify channel 2 remains active
            cfg2 = await self.db.get_channel_config("chan_2")
            self.assertTrue(cfg2 is None or not cfg2.is_disabled)

        asyncio.run(run_test())

    def test_connect_command(self):
        async def run_test():
            res = await self.commands.handle_connect_command("coding_agent_1", "https://gateway.internal:8000")
            self.assertTrue(res["success"])
            self.assertIn("auth_header", res)
            self.assertEqual(res["gateway_status"], "CONNECTED")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
