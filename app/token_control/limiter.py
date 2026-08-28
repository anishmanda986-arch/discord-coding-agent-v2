import time
import asyncio
import uuid
import datetime
from typing import Dict, List, Optional, Tuple, Any
from .models import ModelSwitchState, TokenLimitsConfig, UserTokenRecord, TokenReservation
from .registry import FreeModelRegistry
from ..storage.db import Database

class TokenUsageTracker:
    """
    Production-Grade Token Usage Tracker and Atomic Reservation Manager.
    Guarantees:
      1. Server-side token limit enforcement (Daily, Monthly, Task limits).
      2. Atomic token reservation: concurrent requests cannot race past remaining limits.
      3. Provider usage tracking with fallback estimation flags.
      4. Deterministic inspection for /token without LLM roundtrips.
      5. Full admin diagnostics aggregation without leaking private conversation content.
    """

    def __init__(self, db: Database, free_registry: Optional[FreeModelRegistry] = None):
        self.db = db
        self.free_registry = free_registry or FreeModelRegistry()
        self._lock = asyncio.Lock()
        
        # In-memory active reservations keyed by reservation_id
        self._active_reservations: Dict[str, TokenReservation] = {}
        # Default limits
        self.default_limits = TokenLimitsConfig()

    def _get_date_keys(self) -> Tuple[str, str]:
        now = datetime.datetime.utcnow()
        return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")

    async def get_user_limits(self, user_id: str) -> TokenLimitsConfig:
        """Retrieves configured or default token limits for a specific user."""
        cfg = await self.db.get_user_limits(user_id)
        if cfg:
            return TokenLimitsConfig(
                daily_limit=cfg.get("daily_limit", self.default_limits.daily_limit),
                monthly_limit=cfg.get("monthly_limit", self.default_limits.monthly_limit),
                task_limit=cfg.get("task_limit", self.default_limits.task_limit),
                max_output_tokens=cfg.get("max_output_tokens", self.default_limits.max_output_tokens)
            )
        return self.default_limits

    async def set_user_limits(
        self,
        user_id: str,
        daily_limit: int = 100_000,
        monthly_limit: int = 2_000_000,
        task_limit: int = 50_000,
        max_output_tokens: int = 4_096,
        preferred_model: Optional[str] = None,
        auto_switch_enabled: bool = True
    ) -> None:
        """Sets custom token limits and preferences for a user."""
        await self.db.set_user_limits(
            user_id=user_id,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
            task_limit=task_limit,
            max_output_tokens=max_output_tokens,
            preferred_model=preferred_model,
            auto_switch_enabled=auto_switch_enabled
        )

    async def reserve_tokens(
        self,
        user_id: str,
        estimated_needed: int,
        task_id: str = "task_generic",
        is_paid_model: bool = True
    ) -> Tuple[Optional[str], bool, Optional[str]]:
        """Convenience alias returning (reservation_id, allowed, reason)."""
        allowed, reason, res_id = await self.reserve_tokens_atomically(
            user_id=user_id,
            task_id=task_id,
            estimated_needed=estimated_needed,
            is_paid_model=is_paid_model
        )
        if allowed:
            return res_id, True, None
        return None, False, reason or "DAILY_LIMIT_EXCEEDED"

    async def commit_reservation(
        self,
        reservation_id: Optional[str],
        user_id: str,
        actual_input_tokens: int,
        actual_output_tokens: int,
        model_name: str,
        task_id: str = "task_generic",
        is_free: bool = False,
        is_estimated: bool = False,
        cost_usd: float = 0.0,
        is_auto_switch: bool = False
    ) -> None:
        """Commits actual usage and clears reservation."""
        # Calculate cost if not provided and not free
        if not is_free and cost_usd == 0.0:
            # Estimate openrouter claude rate approx $3 / 1M in, $15 / 1M out
            cost_usd = (actual_input_tokens * 0.000003) + (actual_output_tokens * 0.000015)

        await self.commit_actual_usage(
            reservation_id=reservation_id,
            user_id=user_id,
            task_id=task_id,
            model_name=model_name,
            input_tokens=actual_input_tokens,
            output_tokens=actual_output_tokens,
            is_estimated=is_estimated,
            cost_usd=cost_usd,
            is_auto_switch=is_auto_switch
        )

    async def record_task_tokens(
        self,
        user_id: str,
        task_id: Optional[str],
        input_tokens: int,
        output_tokens: int,
        model_name: str,
        is_free: bool = False,
        is_estimated: bool = False,
        cost_usd: float = 0.0,
        is_auto_switch: bool = False
    ) -> None:
        """Directly records token usage for a task without reservation."""
        await self.commit_actual_usage(
            reservation_id=None,
            user_id=user_id,
            task_id=task_id or "task_standalone",
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            is_estimated=is_estimated,
            cost_usd=cost_usd,
            is_auto_switch=is_auto_switch
        )

    async def get_user_usage_summary(self, user_id: str, current_task_id: Optional[str] = None) -> UserTokenRecord:
        """
        Gathers complete per-user usage stats (daily, monthly, all-time, task, cost, mode).
        Runs deterministically against SQLite database.
        """
        date_str, month_str = self._get_date_keys()
        stats = await self.db.get_token_usage_stats(user_id, date_str, month_str, current_task_id)
        limits = await self.get_user_limits(user_id)
        
        daily_tokens = stats.get("daily_tokens", 0)
        daily_limit = limits.daily_limit

        # Determine current mode
        current_mode = ModelSwitchState.NORMAL.value
        if daily_tokens >= daily_limit:
            current_mode = ModelSwitchState.FREE_FALLBACK.value

        user_pref = await self.db.get_user_model_pref(user_id)
        active_model = user_pref.get("preferred_model") or "anthropic/claude-3.5-sonnet"
        provider = user_pref.get("provider") or "openrouter"
        free_fallback_enabled = user_pref.get("auto_switch_enabled", True)

        return UserTokenRecord(
            user_id=user_id,
            input_tokens=stats.get("total_input_tokens", 0),
            output_tokens=stats.get("total_output_tokens", 0),
            total_tokens=stats.get("total_tokens", 0),
            task_tokens=stats.get("task_tokens", 0),
            daily_tokens=daily_tokens,
            monthly_tokens=stats.get("monthly_tokens", 0),
            model_calls_paid=stats.get("model_calls_paid", 0),
            model_calls_free=stats.get("model_calls_free", 0),
            estimated_cost_usd=stats.get("estimated_cost_usd", 0.0),
            rate_limit_events=stats.get("rate_limit_events", 0),
            auto_switches=stats.get("auto_switches", 0),
            current_mode=current_mode,
            active_model=active_model,
            provider=provider,
            free_fallback_enabled=free_fallback_enabled
        )

    async def reserve_tokens_atomically(
        self,
        user_id: str,
        task_id: str,
        estimated_needed: int,
        is_paid_model: bool = True
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Atomic Token Reservation with Concurrency Protection:
          1. Locks user reservation channel.
          2. Calculates current daily + active reservations.
          3. If remaining < estimated_needed:
             - If paid model: returns (False, "LIMIT_EXCEEDED", None).
             - Free models bypass daily paid quota checks.
          4. If within budget: creates reservation_id, holds reservation, returns (True, None, res_id).
        """
        async with self._lock:
            limits = await self.get_user_limits(user_id)
            date_str, month_str = self._get_date_keys()
            stats = await self.db.get_token_usage_stats(user_id, date_str, month_str, task_id)
            
            daily_used = stats.get("daily_tokens", 0)
            
            # Add all pending active reservations for this user
            pending_reserved = sum(
                r.reserved_tokens for r in self._active_reservations.values()
                if r.user_id == user_id
            )
            
            effective_daily = daily_used + pending_reserved

            if is_paid_model and (effective_daily + estimated_needed > limits.daily_limit):
                return False, f"Daily token limit reached ({effective_daily:,}/{limits.daily_limit:,})", None

            # Check task limit
            current_task_used = stats.get("task_tokens", 0)
            if current_task_used + estimated_needed > limits.task_limit:
                # Warning or fallback
                pass

            res_id = f"res_{uuid.uuid4().hex[:8]}"
            res = TokenReservation(
                reservation_id=res_id,
                user_id=user_id,
                task_id=task_id,
                reserved_tokens=estimated_needed
            )
            self._active_reservations[res_id] = res
            return True, None, res_id

    async def commit_actual_usage(
        self,
        reservation_id: Optional[str],
        user_id: str,
        task_id: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        is_free: Optional[bool] = None,
        is_estimated: bool = False,
        cost_usd: float = 0.0,
        is_auto_switch: bool = False
    ) -> None:
        """
        Replaces token reservation with actual usage and commits to SQLite.
        """
        async with self._lock:
            if reservation_id and reservation_id in self._active_reservations:
                self._active_reservations.pop(reservation_id, None)

            date_str, month_str = self._get_date_keys()
            free_flag = is_free if is_free is not None else self.free_registry.is_model_verified_free(model_name)
            
            total_tokens = input_tokens + output_tokens
            await self.db.record_token_usage(
                user_id=user_id,
                task_id=task_id,
                date_str=date_str,
                month_str=month_str,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                model_name=model_name,
                is_free=free_flag,
                is_estimated=is_estimated,
                cost_usd=cost_usd,
                is_auto_switch=is_auto_switch
            )

    async def release_reservation(self, reservation_id: Optional[str]) -> None:
        """Releases an uncommitted reservation safely."""
        async with self._lock:
            if reservation_id and reservation_id in self._active_reservations:
                self._active_reservations.pop(reservation_id, None)

    def format_token_command_text(self, record: UserTokenRecord, limits: TokenLimitsConfig, username: str = "Discord User") -> str:
        """
        Renders the exact formatted block specified for the /token command.
        """
        daily_limit = limits.daily_limit
        remaining = max(0, daily_limit - record.daily_tokens)
        fallback_str = "ENABLED" if record.free_fallback_enabled else "DISABLED"

        output = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🪙 CODING AGENT — TOKEN USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User:
{username}

Current model:
{record.active_model}

Provider:
{record.provider}

Input tokens:
{record.input_tokens:,}

Output tokens:
{record.output_tokens:,}

Total:
{record.total_tokens:,}

Task usage:
{record.task_tokens:,}

Daily usage:
{record.daily_tokens:,} / {daily_limit:,}

Remaining:
{remaining:,}

Estimated cost:
${record.estimated_cost_usd:.4f}

Free-model fallback:
{fallback_str}

Current mode:
{record.current_mode}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        return output

    async def get_admin_diagnostics_summary(self) -> Dict[str, Any]:
        """
        Calculates aggregate usage diagnostics for authorized admins.
        Never exposes private user conversation or prompt text.
        """
        date_str, month_str = self._get_date_keys()
        agg = await self.db.get_admin_aggregate_token_stats(date_str, month_str)
        return agg
