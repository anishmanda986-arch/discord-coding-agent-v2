import time
from typing import Dict, Any, List, Optional
from ..security.redaction import SecretRedactor

class DiscordEmbedFormatter:
    """
    Constructs high-contrast, professional Discord embeds and status messages.
    Includes ASCII progress bars, files changed counts, test badges, and cost summaries.
    Ensures secrets are 100% redacted.
    """

    @staticmethod
    def render_progress_bar(percentage: int, total_blocks: int = 10) -> str:
        pct = max(0, min(100, percentage))
        filled_blocks = int(round((pct / 100.0) * total_blocks))
        empty_blocks = total_blocks - filled_blocks
        return f"{'█' * filled_blocks}{'░' * empty_blocks} {pct}%"

    @classmethod
    def create_progress_embed(
        cls,
        task_id: str,
        project_name: str,
        stage: str,
        current_action: str,
        progress_pct: int,
        files_count: int = 0,
        model_name: str = "gpt-4o",
        test_status: str = "Pending"
    ) -> Dict[str, Any]:
        progress_bar = cls.render_progress_bar(progress_pct)
        
        embed = {
            "title": "CODING AGENT",
            "color": 0x3B82F6,  # Blue
            "description": f"**Project:** {SecretRedactor.redact_text(project_name)}\n**Status:** `{stage.upper()}`\n\n{progress_bar}",
            "fields": [
                {"name": "Current Activity", "value": SecretRedactor.redact_text(current_action), "inline": False},
                {"name": "Files Changed", "value": f"`{files_count}` files", "inline": True},
                {"name": "Tests", "value": f"`{test_status}`", "inline": True},
                {"name": "Model", "value": f"`{model_name}`", "inline": True}
            ],
            "footer": {"text": f"Task ID: {task_id[:8]}... | Multi-Agent Gateway"}
        }
        return embed

    @classmethod
    def create_completion_embed(
        cls,
        task_id: str,
        summary: str,
        files_changed: List[str],
        test_result: Dict[str, Any],
        duration_sec: float,
        metrics: Dict[str, Any],
        zip_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        files_list = "\n".join([f"• `{f}`" for f in files_changed[:6]])
        if len(files_changed) > 6:
            files_list += f"\n*...and {len(files_changed)-6} more files*"
        if not files_list:
            files_list = "• `No files modified`"

        test_passed = test_result.get("passed", True)
        test_badge = "✅ Passed" if test_passed else "⚠️ Warnings / Failures"

        embed = {
            "title": "✅ TASK COMPLETED",
            "color": 0x10B981,  # Emerald Green
            "description": f"**Summary:**\n{SecretRedactor.redact_text(summary)}",
            "fields": [
                {"name": "Files Changed", "value": files_list, "inline": False},
                {"name": "Tests", "value": f"`{test_badge}`\n_{test_result.get('details', '')[:100]}_", "inline": True},
                {"name": "Execution Time", "value": f"`{round(duration_sec, 2)}s`", "inline": True},
                {
                    "name": "API & Token Usage",
                    "value": f"Input: `{metrics.get('input_tokens', 0):,}`\nOutput: `{metrics.get('output_tokens', 0):,}`\nEst. Cost: `${metrics.get('estimated_cost_usd', 0.0):.4f}`",
                    "inline": True
                }
            ],
            "footer": {"text": f"Deliverable: {zip_filename or 'workspace.zip'} ready for download."}
        }
        return embed

    @classmethod
    def create_failure_embed(
        cls,
        task_id: str,
        stage: str,
        actual_error: str,
        attempted_actions: str,
        recommended_action: str
    ) -> Dict[str, Any]:
        embed = {
            "title": "❌ TASK FAILED",
            "color": 0xEF4444,  # Red
            "description": f"The coding agent stopped at stage `{stage.upper()}`.",
            "fields": [
                {"name": "Actual Error", "value": f"```{SecretRedactor.redact_text(actual_error[:400])}```", "inline": False},
                {"name": "What was attempted", "value": SecretRedactor.redact_text(attempted_actions[:300]), "inline": False},
                {"name": "Recommended Action", "value": SecretRedactor.redact_text(recommended_action[:250]), "inline": False}
            ],
            "footer": {"text": f"Task ID: {task_id} | Security & Budget Guardian"}
        }
        return embed

    @classmethod
    def create_token_embed(
        cls,
        user_name: str,
        active_model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        task_tokens: int,
        daily_tokens: int,
        daily_limit: int,
        remaining_tokens: int,
        estimated_cost_usd: float,
        free_fallback_enabled: bool,
        current_mode: str
    ) -> Dict[str, Any]:
        embed = {
            "title": "🪙 CODING AGENT — TOKEN USAGE",
            "color": 0xF59E0B,  # Amber
            "description": f"**User:** `{SecretRedactor.redact_text(user_name)}`\n**Current Model:** `{active_model}`\n**Provider:** `{provider}`",
            "fields": [
                {"name": "Input Tokens", "value": f"`{input_tokens:,}`", "inline": True},
                {"name": "Output Tokens", "value": f"`{output_tokens:,}`", "inline": True},
                {"name": "Total Tokens", "value": f"`{total_tokens:,}`", "inline": True},
                {"name": "Task Usage", "value": f"`{task_tokens:,}`", "inline": True},
                {"name": "Daily Usage", "value": f"`{daily_tokens:,} / {daily_limit:,}`", "inline": True},
                {"name": "Remaining Quota", "value": f"`{remaining_tokens:,}`", "inline": True},
                {"name": "Estimated Cost", "value": f"`${estimated_cost_usd:.4f}`", "inline": True},
                {"name": "Free-Model Fallback", "value": f"`{'ENABLED' if free_fallback_enabled else 'DISABLED'}`", "inline": True},
                {"name": "Current Mode", "value": f"`{current_mode}`", "inline": True}
            ],
            "footer": {"text": "Multi-Agent Token & Quota Control"}
        }
        return embed

    @classmethod
    def create_switch_embed(
        cls,
        current_model: str,
        auto_switch: bool,
        free_models: List[str],
        paid_fallback: str = "DISABLED"
    ) -> Dict[str, Any]:
        models_formatted = "\n".join([f"✓ `{m}`" for m in free_models]) if free_models else "• *None verified*"
        embed = {
            "title": "🔄 MODEL ROUTER",
            "color": 0x6366F1,  # Indigo
            "description": f"**Current Model:** `{current_model}`\n**Fallback:** `FREE MODEL`\n**Auto-Switch:** `{'ON' if auto_switch else 'OFF'}`",
            "fields": [
                {"name": "Free Models Available", "value": models_formatted, "inline": False},
                {"name": "Paid Fallback Policy", "value": f"`{paid_fallback}`", "inline": True}
            ],
            "footer": {"text": "Fail-Closed Zero-Cost Fallback Policy Enforced"}
        }
        return embed

    @classmethod
    def create_limit_switch_embed(
        cls,
        free_model_id: str
    ) -> Dict[str, Any]:
        embed = {
            "title": "⚠️ TOKEN LIMIT REACHED — AUTO-SWITCH",
            "color": 0xEAB308,  # Yellow
            "description": (
                "Your configured token limit has been reached.\n\n"
                f"I've automatically switched this task to:\n"
                f"🆓 **`{free_model_id}`**\n\n"
                "_Only verified free models are allowed as fallback. Task checkpoint preserved._"
            ),
            "footer": {"text": "Multi-Agent Token & Quota Protection"}
        }
        return embed

    @classmethod
    def create_no_free_model_embed(
        cls,
        task_id: str
    ) -> Dict[str, Any]:
        embed = {
            "title": "🛑 TASK STOPPED — TOKEN LIMIT EXCEEDED",
            "color": 0xEF4444,  # Red
            "description": (
                "Your token limit has been reached.\n\n"
                "**No compatible verified free model is currently available for this task.**\n\n"
                "The task has been safely halted to prevent unexpected costs or policy violations."
            ),
            "footer": {"text": f"Task ID: {task_id} | Fail-Closed Safety Stop"}
        }
        return embed

    @classmethod
    def create_token_admin_embed(
        cls,
        admin_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        embed = {
            "title": "📊 TOKEN ADMIN DIAGNOSTICS",
            "color": 0x8B5CF6,  # Purple
            "description": "Aggregate cross-user usage and model router metrics (Private content protected):",
            "fields": [
                {"name": "Total Users", "value": f"`{admin_metrics.get('total_users', 0)}`", "inline": True},
                {"name": "Active Today", "value": f"`{admin_metrics.get('active_users_today', 0)}`", "inline": True},
                {"name": "Tokens Today", "value": f"`{admin_metrics.get('tokens_today', 0):,}`", "inline": True},
                {"name": "Tokens This Month", "value": f"`{admin_metrics.get('tokens_this_month', 0):,}`", "inline": True},
                {"name": "Model Calls", "value": f"`{admin_metrics.get('model_calls', 0):,}`", "inline": True},
                {"name": "Free / Paid Calls", "value": f"`{admin_metrics.get('free_model_calls', 0)}` / `{admin_metrics.get('paid_model_calls', 0)}`", "inline": True},
                {"name": "Cache Hit Rate", "value": f"`{admin_metrics.get('cache_hit_rate', '0%')}`", "inline": True},
                {"name": "Avg Tokens/Task", "value": f"`{admin_metrics.get('average_tokens_per_task', 0):,}`", "inline": True},
                {"name": "Avg Cost/Task", "value": f"`${admin_metrics.get('average_cost_per_task_usd', 0.0):.4f}`", "inline": True},
                {"name": "Rate Limit Events", "value": f"`{admin_metrics.get('rate_limit_events', 0)}`", "inline": True},
                {"name": "Automatic Switches", "value": f"`{admin_metrics.get('automatic_switches', 0)}`", "inline": True}
            ],
            "footer": {"text": "Administrator Token Governance & Analytics"}
        }
        return embed

