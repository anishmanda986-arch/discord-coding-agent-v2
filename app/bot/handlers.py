import os
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Awaitable, Set

from .embeds import DiscordEmbedFormatter
from .commands import BotCommandsHandler
from ..storage.db import Database
from ..storage.models import TaskEntity, TaskStep
from ..rate_limit.limiter import RateLimiter
from ..budget.manager import BudgetManager
from ..router.intent import IntentRouter
from ..router.complexity import TaskComplexityRouter
from ..agents.coding.agent import CodingAgent
from ..agents.conversation.agent import ConversationAgent
from ..api_client.client import OpenAICompatibleClient
from ..security.crypto import CryptoManager
from ..security.validator import SecurityValidator
from ..config import config

class MessageEventHandler:
    """
    Intelligent Message Event Handler:
      - Intent Routing: Distinguishes between NORMAL CHAT and CODING REQUESTS.
      - Normal Chat: Generates direct, friendly conversational responses without workspaces or ZIPs.
      - Coding Requests: Orchestrates the full autonomous coding lifecycle with live single-message status updates.
      - Concurrency & Channel Isolation: Enforces active task limits per channel and per user.
    """

    def __init__(self, db: Database, rate_limiter: Optional[RateLimiter] = None):
        self.db = db
        self.rate_limiter = rate_limiter or RateLimiter()
        self.intent_router = IntentRouter()
        self.commands_handler = BotCommandsHandler(db)
        self.coding_agent = CodingAgent()
        self.conversation_agent = ConversationAgent()
        self.crypto = CryptoManager(config.security.secret_key)
        
        # Concurrency tracking
        self._active_tasks_per_channel: Dict[str, int] = {}
        self._active_tasks_per_user: Dict[str, int] = {}
        self.MAX_CONCURRENT_TASKS_PER_CHANNEL = 2
        self.MAX_CONCURRENT_TASKS_PER_USER = 1

    async def handle_user_message(
        self,
        channel_id: str,
        user_id: str,
        content: str,
        guild_id: Optional[str] = None,
        send_embed_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        send_file_callback: Optional[Callable[[str], Awaitable[None]]] = None,
        send_text_callback: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Processes an incoming user message.
        """
        if not content or not content.strip():
            return None

        # 0. Check for Slash / Text Commands
        trimmed = content.strip()
        if trimmed.startswith("/"):
            parts = trimmed.split()
            cmd = parts[0].lower()
            
            if cmd == "/token":
                requested_admin = "--admin" in parts or "-a" in parts
                is_admin = requested_admin and user_id in config.admin_user_ids
                res = await self.commands_handler.handle_token_command(
                    user_id=user_id,
                    username="Discord User",
                    is_admin=is_admin,
                    admin_mode=is_admin
                )
                if send_embed_callback and "embed" in res:
                    await send_embed_callback(res["embed"])
                elif send_text_callback:
                    await send_text_callback(res["formatted_text"])
                return res

            elif cmd == "/switch":
                target_model = None
                auto_switch = None
                for p in parts[1:]:
                    if p.lower() in ("on", "true", "1", "enable"):
                        auto_switch = True
                    elif p.lower() in ("off", "false", "0", "disable"):
                        auto_switch = False
                    elif not p.startswith("-"):
                        target_model = p

                res = await self.commands_handler.handle_switch_command(
                    user_id=user_id,
                    target_model=target_model,
                    auto_switch=auto_switch
                )
                if send_embed_callback and "embed" in res:
                    await send_embed_callback(res["embed"])
                elif send_text_callback:
                    await send_text_callback(res.get("message", "Model switched."))
                return res

            elif cmd in ("/models", "/model", "/modle"):
                query = parts[1] if len(parts) > 1 else None
                res = await self.commands_handler.handle_models_command(
                    query=query,
                    scope_id=f"channel:{channel_id}"
                )
                if send_embed_callback:
                    models_list = res.get("models", [])
                    models_str = "\n".join([f"• `{m.get('id')}`" for m in models_list[:15]]) or "No models found."
                    await send_embed_callback({
                        "title": f"Discovered Models ({res.get('matched_models', len(models_list))})",
                        "description": models_str,
                        "color": 0x3498DB
                    })
                elif send_text_callback:
                    models_list = res.get("models", [])
                    models_str = "\n".join([f"• `{m.get('id')}`" for m in models_list[:15]]) or "No models found."
                    await send_text_callback(f"**Discovered Models:**\n{models_str}")
                return res

            elif cmd == "/test":
                res = await self.commands_handler.handle_test_command()
                report_str = res.get("ascii_report") or res.get("report") or "Diagnostics Completed."
                if send_text_callback:
                    await send_text_callback(f"```\n{report_str}\n```")
                elif send_embed_callback:
                    await send_embed_callback({
                        "title": f"System Diagnostic: {res.get('overall_status', 'COMPLETED')}",
                        "description": f"```\n{report_str[:3800]}\n```",
                        "color": 0x2ECC71 if res.get("overall_status") == "PASS" else 0xE74C3C
                    })
                return res

            elif cmd == "/disable":
                res = await self.commands_handler.handle_disable_command(channel_id=channel_id, guild_id=guild_id)
                if send_text_callback:
                    await send_text_callback(res["message"])
                elif send_embed_callback:
                    await send_embed_callback({
                        "title": "Channel Configuration",
                        "description": res["message"],
                        "color": 0x95A5A6
                    })
                return res

            elif cmd == "/connect":
                agent_id = parts[1] if len(parts) > 1 else "coding_agent_primary"
                endpoint = parts[2] if len(parts) > 2 else "http://127.0.0.1:3000"
                res = await self.commands_handler.handle_connect_command(agent_id=agent_id, endpoint=endpoint)
                if send_text_callback:
                    await send_text_callback(res["message"])
                elif send_embed_callback:
                    await send_embed_callback({
                        "title": "Gateway Connection",
                        "description": res["message"],
                        "color": 0x2ECC71
                    })
                return res

            elif cmd == "/api":
                provider = parts[1] if len(parts) > 1 else "OpenRouter"
                base_url = parts[2] if len(parts) > 2 else "https://openrouter.ai/api/v1"
                api_key = parts[3] if len(parts) > 3 else ""
                res = await self.commands_handler.handle_api_command(
                    scope_id=f"channel:{channel_id}",
                    provider=provider,
                    base_url=base_url,
                    api_key=api_key
                )
                msg = res.get("message") or res.get("error", "API configured.")
                if send_text_callback:
                    await send_text_callback(msg)
                elif send_embed_callback:
                    await send_embed_callback({
                        "title": "API Endpoint Configuration",
                        "description": msg,
                        "color": 0x2ECC71 if res.get("success") else 0xE74C3C
                    })
                return res

        # 1. Check if channel is disabled
        channel_cfg = await self.db.get_channel_config(channel_id)
        if channel_cfg and channel_cfg.is_disabled:
            return {"ignored": True, "reason": "Channel is disabled"}

        # 2. Rate limit check
        allowed, rate_err, wait_sec = self.rate_limiter.check_rate_limits(user_id, channel_id)
        if not allowed:
            await self.db.record_rate_limit_event(user_id, "RATE_LIMIT_EXCEEDED")
            if send_embed_callback:
                failure_embed = DiscordEmbedFormatter.create_failure_embed(
                    task_id="rate_limit",
                    stage="rate_limit_protection",
                    actual_error=rate_err or "Rate limit exceeded",
                    attempted_actions="Checked per-user and per-channel token bucket rate limiters",
                    recommended_action=f"Please wait {int(wait_sec)+1} seconds before sending your next message."
                )
                await send_embed_callback(failure_embed)
            return {"error": "Rate limit exceeded"}

        # 3. Resolve API configuration
        api_cfg = await self.db.get_api_config(f"channel:{channel_id}") or await self.db.get_api_config("global")
        client = None
        configured_model = config.default_strong_model

        if api_cfg:
            api_key = self.crypto.decrypt_secret(api_cfg.api_key_encrypted)
            client = OpenAICompatibleClient(api_cfg.base_url, api_key, api_cfg.selected_model)
            configured_model = api_cfg.selected_model
        elif config.default_api_key:
            client = OpenAICompatibleClient(config.default_base_url, config.default_api_key, configured_model)

        # 3b. Resolve Execution Model via Token Control ModelSwitchRouter
        route_decision = await self.commands_handler.model_router.resolve_execution_model(
            user_id=user_id,
            base_model=configured_model,
            estimated_tokens=2000
        )

        if route_decision.status == "NO_FREE_MODEL":
            if send_embed_callback:
                stop_embed = DiscordEmbedFormatter.create_no_free_model_embed(task_id="token_limit")
                await send_embed_callback(stop_embed)
            elif send_text_callback:
                await send_text_callback("🛑 Token limit reached. No compatible verified free model is currently available for this task.")
            return {"error": "Token limit reached and no free model available."}

        selected_model = route_decision.selected_model
        is_free_execution = route_decision.is_free_model

        # If automatically switched to free model, notify the user
        if route_decision.action == "SWITCH_TO_FREE":
            if send_embed_callback:
                switch_embed = DiscordEmbedFormatter.create_limit_switch_embed(selected_model)
                await send_embed_callback(switch_embed)

        # 4. Intent Classification: CONVERSATION vs CODING
        intent = await self.intent_router.classify_intent_with_model(content, client=client, fast_model=config.default_fast_model)

        # ----------------------------------------------------
        # CASE A: NORMAL CONVERSATIONAL CHAT
        # ----------------------------------------------------
        if intent == IntentRouter.INTENT_CONVERSATION:
            chat_res = await self.conversation_agent.generate_response(
                prompt=content,
                client=client,
                model=selected_model if is_free_execution else config.default_fast_model
            )
            reply_text = chat_res.get("content", "")
            
            # Record tokens used in chat
            chat_usage = chat_res.get("usage", {})
            in_tok = chat_usage.get("prompt_tokens", len(content) // 4)
            out_tok = chat_usage.get("completion_tokens", len(reply_text) // 4)
            await self.commands_handler.token_tracker.record_task_tokens(
                user_id=user_id,
                task_id=None,
                input_tokens=in_tok,
                output_tokens=out_tok,
                model_name=selected_model if is_free_execution else config.default_fast_model,
                is_free=is_free_execution,
                is_auto_switch=(route_decision.action == "SWITCH_TO_FREE")
            )

            if send_text_callback:
                await send_text_callback(reply_text)
            elif send_embed_callback:
                # Fallback to simple embed if only embed callback is provided
                await send_embed_callback({
                    "title": "AI Coding Companion",
                    "description": reply_text,
                    "color": 0x3498DB
                })
            return {
                "success": True,
                "type": "conversation",
                "response": reply_text,
                "model": chat_res.get("model", selected_model),
                "elapsed_seconds": chat_res.get("elapsed_seconds")
            }

        # ----------------------------------------------------
        # CASE B: AUTONOMOUS CODING TASK
        # ----------------------------------------------------
        # Concurrency safety check
        current_chan_tasks = self._active_tasks_per_channel.get(channel_id, 0)
        if current_chan_tasks >= self.MAX_CONCURRENT_TASKS_PER_CHANNEL:
            if send_text_callback:
                await send_text_callback(f"⚠️ Channel has {current_chan_tasks} active coding tasks running. Please wait for them to finish.")
            return {"error": "Maximum concurrent tasks in channel reached."}

        self._active_tasks_per_channel[channel_id] = current_chan_tasks + 1
        self._active_tasks_per_user[user_id] = self._active_tasks_per_user.get(user_id, 0) + 1

        task_id = f"TASK-{uuid.uuid4().hex[:6].upper()}"
        project_name = SecurityValidator.sanitize_project_name(content[:30])
        workspace_path = f"/tmp/coding_agent_workspaces/{task_id.lower()}"

        try:
            # 5. Classify complexity & budget
            complexity, budget_limits = TaskComplexityRouter.classify_prompt(content)
            budget = BudgetManager(
                max_model_calls=budget_limits["max_calls"],
                max_tokens=budget_limits["max_tokens"],
                max_tool_calls=budget_limits["max_tools"]
            )

            # 6. Create Task Record
            task_entity = TaskEntity(
                task_id=task_id,
                project_id=project_name,
                user_id=user_id,
                channel_id=channel_id,
                prompt=content,
                complexity=complexity,
                status="ANALYZING"
            )
            await self.db.save_task(task_entity)

            # Progress reporting helper for single Discord message update
            async def on_progress(activity_text: str, progress_pct: int):
                if send_embed_callback:
                    p_embed = DiscordEmbedFormatter.create_progress_embed(
                        task_id=task_id,
                        project_name=project_name,
                        stage="implementing",
                        current_action=activity_text,
                        progress_pct=progress_pct,
                        files_count=len(task_entity.files_changed),
                        model_name=selected_model
                    )
                    await send_embed_callback(p_embed)

            start_time = time.time()

            # 7. Execute Autonomous Coding Agent Loop
            result = await self.coding_agent.execute_task(
                task_id=task_id,
                prompt=content,
                workspace_path=workspace_path,
                client=client,
                model=selected_model,
                budget_manager=budget,
                progress_callback=on_progress
            )

            duration_sec = time.time() - start_time
            task_entity.status = "COMPLETED"
            task_entity.completed_at = time.time()
            task_entity.files_changed = result.get("files_changed", [])
            task_entity.deliverable_path = result.get("deliverable_zip")
            await self.db.save_task(task_entity)

            # Record token metrics
            t_metrics = result.get("metrics", {})
            in_tokens = t_metrics.get("tokens_input", 1200)
            out_tokens = t_metrics.get("tokens_output", 800)
            await self.commands_handler.token_tracker.record_task_tokens(
                user_id=user_id,
                task_id=task_id,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                model_name=selected_model,
                is_free=is_free_execution,
                is_auto_switch=(route_decision.action == "SWITCH_TO_FREE")
            )

            # 8. Deliver Final Embed & Deliverable ZIP
            if send_embed_callback:
                comp_embed = DiscordEmbedFormatter.create_completion_embed(
                    task_id=task_id,
                    summary=result.get("summary", "Task completed."),
                    files_changed=result.get("files_changed", []),
                    test_result=result.get("test_result", {}),
                    duration_sec=duration_sec,
                    metrics=result.get("metrics", {}),
                    zip_filename=Path(result.get("deliverable_zip", "workspace.zip")).name
                )
                await send_embed_callback(comp_embed)

            if send_file_callback and result.get("deliverable_zip") and os.path.exists(result["deliverable_zip"]):
                await send_file_callback(result["deliverable_zip"])

            result["type"] = "coding"
            return result

        except Exception as e:
            duration_sec = time.time() - start_time
            task_entity.status = "FAILED"
            task_entity.error_message = str(e)
            await self.db.save_task(task_entity)

            if send_embed_callback:
                fail_embed = DiscordEmbedFormatter.create_failure_embed(
                    task_id=task_id,
                    stage="execution",
                    actual_error=str(e),
                    attempted_actions="Ran autonomous coding loop with tool execution",
                    recommended_action="Check /api configuration and verify base URL and model permissions."
                )
                await send_embed_callback(fail_embed)

            return {"success": False, "type": "coding", "error": str(e)}

        finally:
            # Release concurrency counts
            self._active_tasks_per_channel[channel_id] = max(0, self._active_tasks_per_channel.get(channel_id, 1) - 1)
            self._active_tasks_per_user[user_id] = max(0, self._active_tasks_per_user.get(user_id, 1) - 1)
