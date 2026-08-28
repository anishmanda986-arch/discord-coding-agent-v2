import time
from typing import Dict, Any

class TelemetryMetrics:
    """
    Tracks real-time system metrics:
      - Total tasks completed & failed
      - Token savings vs naive baseline
      - Cache hit rates
      - Average execution latency
      - Cumulative costs
    """

    def __init__(self):
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.total_tokens_used = 0
        self.total_tokens_saved_by_optimization = 0
        self.total_cost_usd = 0.0
        self.total_tool_calls = 0
        self.total_latency_seconds = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        self.start_time = time.time()

    def record_task_complete(self, tokens_used: int, estimated_naive_tokens: int, duration_sec: float, cost_usd: float, success: bool = True):
        self.total_tasks += 1
        if success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1

        self.total_tokens_used += tokens_used
        saved = max(0, estimated_naive_tokens - tokens_used)
        self.total_tokens_saved_by_optimization += saved
        self.total_latency_seconds += duration_sec
        self.total_cost_usd += cost_usd

    def record_tool_call(self):
        self.total_tool_calls += 1

    def record_cache_event(self, hit: bool):
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def get_metrics_report(self) -> Dict[str, Any]:
        avg_latency = (self.total_latency_seconds / max(1, self.total_tasks))
        total_cache = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / max(1, total_cache)) * 100
        cost_savings_multiplier = round((self.total_tokens_used + self.total_tokens_saved_by_optimization) / max(1, self.total_tokens_used), 2)

        return {
            "uptime_seconds": round(time.time() - self.start_time, 1),
            "total_tasks": self.total_tasks,
            "success_rate_pct": round((self.successful_tasks / max(1, self.total_tasks)) * 100, 1),
            "failed_tasks": self.failed_tasks,
            "total_tokens_used": self.total_tokens_used,
            "total_tokens_saved": self.total_tokens_saved_by_optimization,
            "estimated_cost_reduction_ratio": f"{max(1.0, cost_savings_multiplier)}x",
            "average_task_latency_sec": round(avg_latency, 2),
            "total_cost_usd": round(self.total_cost_usd, 4),
            "cache_hit_rate_pct": round(cache_hit_rate, 1),
            "total_tool_calls": self.total_tool_calls
        }

metrics_collector = TelemetryMetrics()
