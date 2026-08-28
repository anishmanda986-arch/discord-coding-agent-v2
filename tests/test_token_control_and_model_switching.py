import unittest
import tempfile
import shutil
import asyncio
from pathlib import Path

from app.storage.db import Database
from app.token_control.models import FreeModelEntry, TokenLimitsConfig
from app.token_control.registry import FreeModelRegistry
from app.token_control.limiter import TokenUsageTracker
from app.token_control.router import ModelSwitchRouter
from app.bot.commands import BotCommandsHandler
from app.bot.handlers import MessageEventHandler

class TestTokenControlAndModelSwitching(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        db_path = Path(self.tmp_dir) / "test_tokens.sqlite3"
        self.db = Database(str(db_path))
        self.registry = FreeModelRegistry()
        self.tracker = TokenUsageTracker(self.db, self.registry)
        self.router = ModelSwitchRouter(self.db, self.registry, self.tracker)
        self.commands = BotCommandsHandler(self.db)
        self.handler = MessageEventHandler(self.db)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_free_model_registry_fail_closed(self):
        # 1. Known verified free models are recognized
        self.assertTrue(self.registry.is_model_free("meta-llama/llama-3-8b-instruct:free"))
        self.assertTrue(self.registry.is_model_free("google/gemma-2-9b-it:free"))

        # 2. Paid / unknown models are rejected
        self.assertFalse(self.registry.is_model_free("anthropic/claude-3.5-sonnet"))
        self.assertFalse(self.registry.is_model_free("openai/gpt-4o"))
        self.assertFalse(self.registry.is_model_free("some/unverified-model"))

        # 3. Dynamic verification with explicit 0.0 pricing metadata
        free_meta = {
            "id": "custom/zero-cost-model",
            "pricing": {"prompt": "0", "completion": "0"}
        }
        verified = self.registry.verify_and_register_from_metadata(free_meta)
        self.assertTrue(verified)
        self.assertTrue(self.registry.is_model_free("custom/zero-cost-model"))

        # 4. Fail-closed: non-zero pricing rejected even if name has 'free'
        fake_free_meta = {
            "id": "malicious/free-looking-model",
            "pricing": {"prompt": "0.001", "completion": "0.002"}
        }
        rejected = self.registry.verify_and_register_from_metadata(fake_free_meta)
        self.assertFalse(rejected)
        self.assertFalse(self.registry.is_model_free("malicious/free-looking-model"))

    def test_token_usage_tracker_and_reservation(self):
        async def run_test():
            user_id = "user_test_1"
            # Set a daily limit of 5,000 tokens
            await self.tracker.set_user_limits(user_id=user_id, daily_limit=5000)

            # 1. Initial usage should be 0
            usage = await self.tracker.get_user_usage_summary(user_id)
            self.assertEqual(usage.daily_tokens, 0)
            self.assertEqual(usage.current_mode, "NORMAL")

            # 2. Reserve 2,000 tokens (allowed)
            res_id, allowed, reason = await self.tracker.reserve_tokens(user_id, 2000)
            self.assertTrue(allowed)
            self.assertIsNotNone(res_id)

            # 3. Commit reservation with actual 1,500 tokens
            await self.tracker.commit_reservation(
                reservation_id=res_id,
                user_id=user_id,
                actual_input_tokens=1000,
                actual_output_tokens=500,
                model_name="anthropic/claude-3.5-sonnet",
                is_free=False
            )

            # Check updated stats
            usage2 = await self.tracker.get_user_usage_summary(user_id)
            self.assertEqual(usage2.daily_tokens, 1500)
            self.assertEqual(usage2.total_tokens, 1500)
            self.assertGreater(usage2.estimated_cost_usd, 0.0)

            # 4. Try to reserve 4,000 tokens (1500 + 4000 = 5500 > 5000 limit -> Should be rejected!)
            res_id2, allowed2, reason2 = await self.tracker.reserve_tokens(user_id, 4000)
            self.assertFalse(allowed2)
            self.assertIn("Daily token limit reached", reason2)

        asyncio.run(run_test())

    def test_model_switch_router_auto_fallback(self):
        async def run_test():
            user_id = "user_switch_1"
            # Set daily limit to 1,000 tokens
            await self.tracker.set_user_limits(user_id=user_id, daily_limit=1000)

            # Consume 1,200 tokens to exceed daily limit
            await self.tracker.record_task_tokens(
                user_id=user_id,
                task_id="t1",
                input_tokens=800,
                output_tokens=400,
                model_name="anthropic/claude-3.5-sonnet",
                is_free=False
            )

            # Router decision should detect limit reached and auto-switch to verified free model
            decision = await self.router.resolve_execution_model(
                user_id=user_id,
                base_model="anthropic/claude-3.5-sonnet",
                estimated_tokens=500
            )

            self.assertEqual(decision.status, "FREE_FALLBACK")
            self.assertEqual(decision.action, "SWITCH_TO_FREE")
            self.assertTrue(decision.is_free_model)
            self.assertIn(":free", decision.selected_model)

        asyncio.run(run_test())

    def test_token_and_switch_slash_commands(self):
        async def run_test():
            user_id = "user_cmd_1"

            # 1. /token command returns formatted stats and embed
            tok_res = await self.commands.handle_token_command(
                user_id=user_id,
                username="Alice"
            )
            self.assertTrue(tok_res["success"])
            self.assertIn("Alice", tok_res["formatted_text"])
            self.assertIn("🪙 CODING AGENT — TOKEN USAGE", tok_res["embed"]["title"])

            # 2. /switch command with target model
            sw_res = await self.commands.handle_switch_command(
                user_id=user_id,
                target_model="meta-llama/llama-3-8b-instruct:free",
                auto_switch=True
            )
            self.assertTrue(sw_res["success"])
            self.assertEqual(sw_res["current_model"], "meta-llama/llama-3-8b-instruct:free")
            self.assertTrue(sw_res["auto_switch"])
            self.assertIn("🔄 MODEL ROUTER", sw_res["embed"]["title"])

            # 3. Message handler routes /token and /switch commands without calling LLMs
            msg_tok = await self.handler.handle_user_message(
                channel_id="chan_test",
                user_id=user_id,
                content="/token"
            )
            self.assertTrue(msg_tok["success"])

            msg_sw = await self.handler.handle_user_message(
                channel_id="chan_test",
                user_id=user_id,
                content="/switch auto-switch on"
            )
            self.assertTrue(msg_sw["success"])

        asyncio.run(run_test())

    def test_admin_diagnostics_summary(self):
        async def run_test():
            # Record some mock usage across multiple users
            await self.tracker.record_task_tokens(
                user_id="user_a",
                task_id="task_a",
                input_tokens=1000,
                output_tokens=500,
                model_name="anthropic/claude-3.5-sonnet",
                is_free=False
            )
            await self.tracker.record_task_tokens(
                user_id="user_b",
                task_id="task_b",
                input_tokens=2000,
                output_tokens=1000,
                model_name="meta-llama/llama-3-8b-instruct:free",
                is_free=True,
                is_auto_switch=True
            )

            admin_metrics = await self.tracker.get_admin_diagnostics_summary()
            self.assertGreaterEqual(admin_metrics["total_users"], 2)
            self.assertGreaterEqual(admin_metrics["tokens_today"], 4500)
            self.assertEqual(admin_metrics["free_model_calls"], 1)
            self.assertEqual(admin_metrics["paid_model_calls"], 1)
            self.assertEqual(admin_metrics["automatic_switches"], 1)

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
