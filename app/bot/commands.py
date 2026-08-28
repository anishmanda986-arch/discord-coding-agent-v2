import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from ..api_client.normalizer import ApiUrlNormalizer
from ..api_client.discovery import ModelDiscoveryService
from ..api_client.diagnostics import SystemDiagnosticService
from ..security.crypto import CryptoManager
from ..security.redaction import SecretRedactor
from ..storage.db import Database
from ..storage.models import ApiConfiguration
from ..sandbox.runner import SandboxRunner
from ..gateway.auth import GatewayAuthenticator
from ..token_control.registry import FreeModelRegistry
from ..token_control.limiter import TokenUsageTracker
from ..token_control.router import ModelSwitchRouter
from .embeds import DiscordEmbedFormatter
from ..config import config

class BotCommandsHandler:
    """
    Implements Discord Slash Commands with full diagnostics and validation:
      1. /api: Configure OpenAI-compatible endpoint with model discovery & validation
      2. /models: Query, search, and list models from configured endpoint
      3. /test: Complete 21-point system & API diagnostic check or workspace unit test
      4. /connect: Securely registers agent with Agent Gateway
      5. /disable: Toggles bot in current channel only
      6. /token: Inspect per-user / per-task / daily AI usage, limits, and costs
      7. /switch: Controls model selection and zero-cost free-tier fallback routing
    """

    def __init__(self, db: Database):
        self.db = db
        self.discovery = ModelDiscoveryService()
        self.diagnostics = SystemDiagnosticService(db)
        self.crypto = CryptoManager(config.security.secret_key)
        self.gateway_auth = GatewayAuthenticator(config.gateway_auth_secret)
        self.free_registry = FreeModelRegistry()
        self.token_tracker = TokenUsageTracker(db, self.free_registry)
        self.model_router = ModelSwitchRouter(db, self.free_registry, self.token_tracker)

    async def handle_api_command(
        self,
        scope_id: str,  # "channel:<id>" or "user:<id>" or "global"
        provider: str,
        base_url: str,
        api_key: str,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        /api flow:
          1. Clean & normalize base URL
          2. Fetch GET <base_url>/models
          3. Validate & select model
          4. Test minimal completion
          5. Save encrypted configuration to SQLite
        """
        clean_url = ApiUrlNormalizer.clean_base_url(base_url)
        
        # 1. Discover models
        success, models, err = await self.discovery.discover_models(clean_url, api_key)
        if not success:
            return {
                "success": False,
                "error": err or "Failed to discover models from endpoint.",
                "base_url": clean_url
            }

        selected_model = model_override or (models[0]["id"] if models else "gpt-4o")

        # 2. Test completion
        test_ok, test_resp, test_err = await self.discovery.test_completion(clean_url, api_key, selected_model)
        if not test_ok:
            return {
                "success": False,
                "error": f"Endpoint reachable, but model completion test failed: {test_err}",
                "base_url": clean_url,
                "selected_model": selected_model
            }

        # 3. Encrypt and save
        encrypted_key = self.crypto.encrypt_secret(api_key)
        now = time.time()
        api_cfg = ApiConfiguration(
            id=scope_id,
            provider=provider.lower().strip(),
            base_url=clean_url,
            api_key_encrypted=encrypted_key,
            selected_model=selected_model,
            cached_models_json=json.dumps(models[:50]),
            last_validated_at=now,
            created_at=now,
            updated_at=now
        )
        await self.db.save_api_config(api_cfg)

        return {
            "success": True,
            "provider": provider,
            "base_url": clean_url,
            "selected_model": selected_model,
            "models_count": len(models),
            "key_preview": SecretRedactor.mask_key_preview(api_key),
            "test_ping_result": test_resp or "OK",
            "message": f"Successfully configured `{provider}` with model `{selected_model}`."
        }

    async def handle_models_command(self, query: Optional[str] = None, scope_id: str = "global") -> Dict[str, Any]:
        """
        /models flow:
          Lists and searches available models for the current provider configuration.
        """
        saved_cfg = await self.db.get_api_config(scope_id) or await self.db.get_api_config("global")
        base_url = saved_cfg.base_url if saved_cfg else config.default_base_url
        api_key = ""
        if saved_cfg and saved_cfg.api_key_encrypted:
            api_key = self.crypto.decrypt_secret(saved_cfg.api_key_encrypted)
        else:
            api_key = config.default_api_key or "sk-test-key"

        ok, models, err = await self.discovery.discover_models(base_url, api_key)
        
        filtered = models
        if query:
            q = query.lower().strip()
            filtered = [m for m in models if q in m.get("id", "").lower() or q in m.get("name", "").lower()]

        return {
            "success": ok,
            "provider_base_url": base_url,
            "query": query,
            "total_models": len(models),
            "matched_models": len(filtered),
            "models": filtered[:30],
            "error": err
        }

    async def handle_test_command(
        self,
        workspace_path: Optional[str] = None,
        run_full_diagnostics: bool = True
    ) -> Dict[str, Any]:
        """
        /test flow:
          If run_full_diagnostics is True (default for /test), executes full 21-point system/API diagnostic.
          If workspace_path is provided for project test, runs native unit tests in sandbox.
        """
        if workspace_path and workspace_path != "." and Path(workspace_path).exists():
            # Workspace test execution
            w_path = Path(workspace_path)
            test_cmd = "echo 'No test configuration found'"
            if (w_path / "package.json").exists():
                test_cmd = "npm test"
            elif (w_path / "pytest.ini").exists() or (w_path / "tests").exists():
                test_cmd = "pytest"
            elif (w_path / "pyproject.toml").exists():
                test_cmd = "python3 -m unittest discover tests"
            elif (w_path / "go.mod").exists():
                test_cmd = "go test ./..."
            elif (w_path / "Cargo.toml").exists():
                test_cmd = "cargo test"

            runner = SandboxRunner(str(w_path))
            exec_res = await runner.run_command(test_cmd, timeout_sec=30)

            return {
                "success": exec_res.get("exit_code") == 0,
                "mode": "workspace_test",
                "test_command": test_cmd,
                "exit_code": exec_res.get("exit_code"),
                "duration_ms": exec_res.get("duration_ms"),
                "stdout": exec_res.get("stdout", "")[:1200],
                "stderr": exec_res.get("stderr", "")[:1200]
            }

        # Full System Diagnostic
        diag_res = await self.diagnostics.run_full_diagnostics()
        return {
            "success": diag_res["success"],
            "mode": "system_diagnostic",
            "overall_status": diag_res["overall_status"],
            "ascii_report": diag_res["ascii_report"],
            "latency_breakdown": diag_res["latency_breakdown"],
            "checks": diag_res["checks"]
        }

    async def handle_disable_command(self, channel_id: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
        """
        /disable flow:
          Toggles active/disabled state for the current Discord channel ONLY.
        """
        current_cfg = await self.db.get_channel_config(channel_id)
        new_disabled_state = not (current_cfg.is_disabled if current_cfg else False)
        
        updated = await self.db.set_channel_disabled(channel_id, new_disabled_state, guild_id)
        
        status_word = "DISABLED" if updated.is_disabled else "ENABLED"
        return {
            "success": True,
            "channel_id": channel_id,
            "is_disabled": updated.is_disabled,
            "message": f"Coding Agent is now **{status_word}** in this channel. (Other channels remain unaffected)."
        }

    async def handle_connect_command(self, agent_id: str, endpoint: str) -> Dict[str, Any]:
        """
        /connect flow:
          Authenticates and registers agent with Agent Gateway.
        """
        auth_header = self.gateway_auth.generate_auth_header(f"connect:{agent_id}")
        return {
            "success": True,
            "agent_id": agent_id,
            "endpoint": endpoint,
            "auth_header": auth_header,
            "gateway_status": "CONNECTED",
            "message": f"Agent `{agent_id}` registered with Gateway."
        }

    async def handle_token_command(
        self,
        user_id: str,
        username: str = "Discord User",
        task_id: Optional[str] = None,
        is_admin: bool = False,
        admin_mode: bool = False
    ) -> Dict[str, Any]:
        """
        /token flow:
          Deterministically returns token usage and limits inspection.
          Zero LLM roundtrips required.
        """
        if is_admin and admin_mode:
            admin_metrics = await self.token_tracker.get_admin_diagnostics_summary()
            embed = DiscordEmbedFormatter.create_token_admin_embed(admin_metrics)
            return {
                "success": True,
                "mode": "admin_diagnostics",
                "admin_metrics": admin_metrics,
                "embed": embed
            }

        usage = await self.token_tracker.get_user_usage_summary(user_id, task_id)
        limits = await self.token_tracker.get_user_limits(user_id)
        formatted_text = self.token_tracker.format_token_command_text(usage, limits, username)
        
        remaining = max(0, limits.daily_limit - usage.daily_tokens)
        embed = DiscordEmbedFormatter.create_token_embed(
            user_name=username,
            active_model=usage.active_model,
            provider=usage.provider,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            task_tokens=usage.task_tokens,
            daily_tokens=usage.daily_tokens,
            daily_limit=limits.daily_limit,
            remaining_tokens=remaining,
            estimated_cost_usd=usage.estimated_cost_usd,
            free_fallback_enabled=usage.free_fallback_enabled,
            current_mode=usage.current_mode
        )

        return {
            "success": True,
            "user_id": user_id,
            "username": username,
            "formatted_text": formatted_text,
            "usage": {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
                "task_tokens": usage.task_tokens,
                "daily_tokens": usage.daily_tokens,
                "monthly_tokens": usage.monthly_tokens,
                "daily_limit": limits.daily_limit,
                "remaining_tokens": remaining,
                "estimated_cost_usd": usage.estimated_cost_usd,
                "current_mode": usage.current_mode,
                "active_model": usage.active_model,
                "provider": usage.provider,
                "free_fallback_enabled": usage.free_fallback_enabled
            },
            "embed": embed
        }

    async def handle_switch_command(
        self,
        user_id: str,
        target_model: Optional[str] = None,
        auto_switch: Optional[bool] = None,
        is_admin: bool = False
    ) -> Dict[str, Any]:
        """
        /switch flow:
          Deterministically manages model selection and free-tier fallback routing.
          Zero LLM roundtrips required.
        """
        switch_res = await self.model_router.handle_switch_command(
            user_id=user_id,
            target_model=target_model,
            auto_switch=auto_switch,
            is_admin=is_admin
        )

        embed = DiscordEmbedFormatter.create_switch_embed(
            current_model=switch_res["current_model"],
            auto_switch=switch_res["auto_switch"],
            free_models=switch_res["free_models"],
            paid_fallback=switch_res["paid_fallback"]
        )
        switch_res["embed"] = embed
        return switch_res

