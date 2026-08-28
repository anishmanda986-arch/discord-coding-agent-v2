import time
from typing import Dict, List, Optional, Tuple, Any
from .models import ModelSwitchState, FreeModelEntry, RouteDecision
from .registry import FreeModelRegistry
from .limiter import TokenUsageTracker
from ..storage.db import Database

class ModelSwitchRouter:
    """
    Manages deterministic model routing, per-user model switching, and safe free-tier fallback.
    Guarantees:
      - Deterministic state transitions (NORMAL -> FREE_FALLBACK -> NO_FREE_MODEL / LIMIT_REACHED).
      - Strict fail-closed policy: paid fallback is NEVER used once limits are reached.
      - Free model capability checks prior to fallback execution.
      - Safe task preservation across model switches.
      - Instant response for /switch without LLM calls.
    """

    def __init__(self, db: Database, free_registry: FreeModelRegistry, usage_tracker: TokenUsageTracker):
        self.db = db
        self.free_registry = free_registry
        self.usage_tracker = usage_tracker

    async def resolve_execution_model(
        self,
        user_id: str,
        task_id: str = "task_current",
        requested_model: Optional[str] = None,
        base_model: Optional[str] = None,
        required_capabilities: Optional[List[str]] = None,
        estimated_tokens: int = 2048
    ) -> RouteDecision:
        """
        Determines the model to use for execution.
        Returns: RouteDecision object (also tuple-unpackable)
        """
        caps = required_capabilities or ["chat", "coding", "tool_calling"]
        target_model = requested_model or base_model
        
        # 1. Check user preferences
        user_pref = await self.db.get_user_model_pref(user_id)
        active_model = target_model or user_pref.get("preferred_model") or "anthropic/claude-3.5-sonnet"
        auto_switch_enabled = user_pref.get("auto_switch_enabled", True)

        # 2. Check if active_model is already a verified free model
        is_active_free = self.free_registry.is_model_verified_free(active_model)
        if is_active_free:
            return RouteDecision(
                selected_model=active_model,
                status=ModelSwitchState.NORMAL.value,
                action="PROCEED",
                is_free_model=True,
                notification=None
            )

        # 3. If paid model, check token limits & reserve
        reserved_ok, err, res_id = await self.usage_tracker.reserve_tokens_atomically(
            user_id=user_id,
            task_id=task_id,
            estimated_needed=estimated_tokens,
            is_paid_model=True
        )

        if reserved_ok:
            # Within budget, use selected paid model
            return RouteDecision(
                selected_model=active_model,
                status=ModelSwitchState.NORMAL.value,
                action="PROCEED",
                is_free_model=False,
                notification=None
            )

        # 4. Token limit exceeded! Check if auto-switch is enabled
        if not auto_switch_enabled:
            return RouteDecision(
                selected_model=active_model,
                status=ModelSwitchState.LIMIT_REACHED.value,
                action="STOP",
                is_free_model=False,
                notification="⚠️ Token limit reached and automatic free-model fallback is disabled for your account."
            )

        # 5. Search for a verified compatible free model
        compatible_free_model, reason = self.free_registry.find_compatible_free_model(
            required_capabilities=caps
        )

        if not compatible_free_model:
            # No compatible free model => SAFE STOP
            return RouteDecision(
                selected_model=active_model,
                status=ModelSwitchState.NO_FREE_MODEL.value,
                action="STOP",
                is_free_model=False,
                notification="⚠️ Token limit reached.\nNo compatible verified free model is currently available for this task."
            )

        # 6. Fallback succeeded! Switch to verified free model
        free_model_id = compatible_free_model.model_id
        notification = (
            f"⚠️ Your configured token limit has been reached.\n\n"
            f"I've automatically switched this task to:\n\n"
            f"🆓 `{free_model_id}`\n\n"
            f"Only verified free models are allowed as fallback."
        )
        return RouteDecision(
            selected_model=free_model_id,
            status=ModelSwitchState.FREE_FALLBACK.value,
            action="SWITCH_TO_FREE",
            is_free_model=True,
            notification=notification
        )

    async def handle_switch_command(
        self,
        user_id: str,
        target_model: Optional[str] = None,
        auto_switch: Optional[bool] = None,
        is_admin: bool = False
    ) -> Dict[str, Any]:
        """
        Executes /switch command logic:
          - If target_model or auto_switch specified, updates user preferences.
          - Returns formatted status and available free models.
        """
        # Update user preference if requested
        if target_model is not None or auto_switch is not None:
            await self.db.save_user_model_pref(
                user_id=user_id,
                preferred_model=target_model,
                auto_switch_enabled=auto_switch
            )

        user_pref = await self.db.get_user_model_pref(user_id)
        current_model = user_pref.get("preferred_model") or "anthropic/claude-3.5-sonnet"
        auto_switch_on = user_pref.get("auto_switch_enabled", True)
        
        free_models = self.free_registry.get_all_verified_free_models()
        free_models_list = [f"✓ {m.model_id}" for m in free_models]

        text_output = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 MODEL ROUTER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current:
{current_model}

Fallback:
FREE MODEL

Auto-switch:
{'ON' if auto_switch_on else 'OFF'}

Free models available:
{chr(10).join(free_models_list) if free_models_list else 'None verified'}

Paid fallback:
DISABLED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

        return {
            "success": True,
            "current_model": current_model,
            "fallback": "FREE MODEL",
            "auto_switch": auto_switch_on,
            "free_models": [m.model_id for m in free_models],
            "paid_fallback": "DISABLED",
            "formatted_text": text_output
        }
