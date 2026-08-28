import unittest
import time
from app.rate_limit.limiter import RateLimiter, TokenBucket
from app.budget.manager import BudgetManager

class TestRateLimiterAndBudget(unittest.TestCase):
    def test_token_bucket_consumption(self):
        bucket = TokenBucket(rate_per_minute=60, capacity=2)
        
        # 1st consume
        ok1, wait1 = bucket.consume(1.0)
        self.assertTrue(ok1)
        self.assertEqual(wait1, 0.0)

        # 2nd consume
        ok2, wait2 = bucket.consume(1.0)
        self.assertTrue(ok2)

        # 3rd consume should fail without wait
        ok3, wait3 = bucket.consume(1.0)
        self.assertFalse(ok3)
        self.assertGreater(wait3, 0.0)

    def test_multi_tier_rate_limiter(self):
        limiter = RateLimiter(global_rpm=10, user_rpm=2, channel_rpm=5)
        
        # User 1 first 2 calls allowed
        ok1, _, _ = limiter.check_rate_limits("user_123", "chan_abc")
        self.assertTrue(ok1)

        ok2, _, _ = limiter.check_rate_limits("user_123", "chan_abc")
        self.assertTrue(ok2)

        # User 1 3rd call rejected by per-user limit
        ok3, err, _ = limiter.check_rate_limits("user_123", "chan_abc")
        self.assertFalse(ok3)
        self.assertIn("User rate limit exceeded", err)

        # User 2 in same channel allowed
        ok4, _, _ = limiter.check_rate_limits("user_456", "chan_abc")
        self.assertTrue(ok4)

    def test_budget_manager_limits_and_tracking(self):
        budget = BudgetManager(max_model_calls=3, max_tokens=1000, cost_ceiling_usd=0.05)
        
        budget.record_model_usage(input_tokens=200, output_tokens=100, model_type="strong")
        budget.record_tool_call()
        
        within, _ = budget.check_limits()
        self.assertTrue(within)

        # Record beyond limits
        budget.record_model_usage(input_tokens=800, output_tokens=500, model_type="strong")
        within2, reason = budget.check_limits()
        self.assertFalse(within2)
        self.assertIn("token budget exceeded", reason)

        summary = budget.get_summary()
        self.assertEqual(summary["model_calls"], 2)
        self.assertEqual(summary["tool_calls"], 1)
        self.assertGreater(summary["estimated_cost_usd"], 0.0)

if __name__ == "__main__":
    unittest.main()
