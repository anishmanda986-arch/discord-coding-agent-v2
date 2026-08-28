import time
from typing import Dict, Any, Tuple, Optional

class BudgetManager:
    """
    Monitors and enforces token budgets, execution timeouts, and cost ceilings.
    Prevents run-away agent loops and credit exhaustion.
    """

    # Estimated pricing per 1k tokens for tracking (USD)
    MODEL_PRICING = {
        "fast": {"input": 0.0001, "output": 0.0004},      # e.g., gemini-flash, gpt-4o-mini
        "strong": {"input": 0.003, "output": 0.015},      # e.g., claude-3.5-sonnet, gpt-4o
        "default": {"input": 0.001, "output": 0.003}
    }

    def __init__(
        self,
        max_model_calls: int = 25,
        max_tokens: int = 150_000,
        max_tool_calls: int = 40,
        max_execution_time_sec: int = 300,
        cost_ceiling_usd: float = 1.00
    ):
        self.max_model_calls = max_model_calls
        self.max_tokens = max_tokens
        self.max_tool_calls = max_tool_calls
        self.max_execution_time_sec = max_execution_time_sec
        self.cost_ceiling_usd = cost_ceiling_usd

        # State tracking
        self.start_time = time.time()
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.model_calls_count = 0
        self.tool_calls_count = 0
        self.estimated_cost_usd = 0.0

    def record_model_usage(self, input_tokens: int, output_tokens: int, model_type: str = "strong") -> None:
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.model_calls_count += 1

        pricing = self.MODEL_PRICING.get(model_type, self.MODEL_PRICING["default"])
        cost = (input_tokens / 1000.0 * pricing["input"]) + (output_tokens / 1000.0 * pricing["output"])
        self.estimated_cost_usd += cost

    def record_tool_call(self) -> None:
        self.tool_calls_count += 1

    def check_limits(self) -> Tuple[bool, Optional[str]]:
        """
        Returns (within_budget: bool, failure_reason: Optional[str])
        """
        elapsed = time.time() - self.start_time
        if elapsed > self.max_execution_time_sec:
            return False, f"Execution timeout exceeded ({int(elapsed)}s > {self.max_execution_time_sec}s)."

        if self.model_calls_count > self.max_model_calls:
            return False, f"Maximum model calls limit reached ({self.model_calls_count}/{self.max_model_calls})."

        total_tokens = self.total_input_tokens + self.total_output_tokens
        if total_tokens > self.max_tokens:
            return False, f"Maximum token budget exceeded ({total_tokens:,} > {self.max_tokens:,})."

        if self.tool_calls_count > self.max_tool_calls:
            return False, f"Maximum tool calls limit exceeded ({self.tool_calls_count}/{self.max_tool_calls})."

        if self.estimated_cost_usd > self.cost_ceiling_usd:
            return False, f"Cost safety ceiling reached (${self.estimated_cost_usd:.3f} > ${self.cost_ceiling_usd:.2f})."

        return True, None

    def should_compress_context(self) -> bool:
        """Triggers context compression if 70% of token budget or 60% of model calls consumed."""
        total_tokens = self.total_input_tokens + self.total_output_tokens
        return (total_tokens > self.max_tokens * 0.7) or (self.model_calls_count > self.max_model_calls * 0.6)

    def get_summary(self) -> Dict[str, Any]:
        elapsed = time.time() - self.start_time
        total_tokens = self.total_input_tokens + self.total_output_tokens
        return {
            "elapsed_seconds": round(elapsed, 2),
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": total_tokens,
            "model_calls": self.model_calls_count,
            "tool_calls": self.tool_calls_count,
            "estimated_cost_usd": round(self.estimated_cost_usd, 4)
        }
