import time
import asyncio
from typing import Dict, Tuple, Optional

class TokenBucket:
    def __init__(self, rate_per_minute: int, capacity: Optional[int] = None):
        self.rate_per_sec = rate_per_minute / 60.0
        self.capacity = capacity or rate_per_minute
        self.tokens = float(self.capacity)
        self.last_update = time.time()

    def consume(self, amount: float = 1.0) -> Tuple[bool, float]:
        """
        Consumes tokens if available.
        Returns: (allowed: bool, wait_time_seconds: float)
        """
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        # Replenish tokens
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_sec)

        if self.tokens >= amount:
            self.tokens -= amount
            return True, 0.0
        else:
            needed = amount - self.tokens
            wait_time = needed / self.rate_per_sec
            return False, wait_time


class RateLimiter:
    """
    Multi-tiered rate limiter for Discord Coding Agent:
      - Global rate limit
      - Per-User rate limit
      - Per-Channel rate limit
      - Per-Provider concurrency limiter
    """

    def __init__(self, global_rpm: int = 120, user_rpm: int = 20, channel_rpm: int = 30):
        self.global_bucket = TokenBucket(global_rpm)
        self.user_buckets: Dict[str, TokenBucket] = {}
        self.channel_buckets: Dict[str, TokenBucket] = {}
        self.user_rpm = user_rpm
        self.channel_rpm = channel_rpm
        self._provider_semaphores: Dict[str, asyncio.Semaphore] = {}

    def check_rate_limits(self, user_id: str, channel_id: str) -> Tuple[bool, Optional[str], float]:
        """
        Checks if the request is within rate limits.
        Returns: (allowed, error_reason, wait_seconds)
        """
        # Global check
        g_allowed, g_wait = self.global_bucket.consume(1.0)
        if not g_allowed:
            return False, "Global rate limit exceeded. Please try again shortly.", g_wait

        # Channel check
        if channel_id not in self.channel_buckets:
            self.channel_buckets[channel_id] = TokenBucket(self.channel_rpm)
        c_allowed, c_wait = self.channel_buckets[channel_id].consume(1.0)
        if not c_allowed:
            return False, f"Channel rate limit exceeded. Wait {int(c_wait)+1}s.", c_wait

        # User check
        if user_id not in self.user_buckets:
            self.user_buckets[user_id] = TokenBucket(self.user_rpm)
        u_allowed, u_wait = self.user_buckets[user_id].consume(1.0)
        if not u_allowed:
            return False, f"User rate limit exceeded ({self.user_rpm} requests/min). Wait {int(u_wait)+1}s.", u_wait

        return True, None, 0.0

    def get_provider_semaphore(self, provider: str, max_concurrent: int = 5) -> asyncio.Semaphore:
        if provider not in self._provider_semaphores:
            self._provider_semaphores[provider] = asyncio.Semaphore(max_concurrent)
        return self._provider_semaphores[provider]
