import unittest
import asyncio
from app.api_client.discovery import ModelDiscoveryService

class TestModelDiscovery(unittest.TestCase):
    def setUp(self):
        self.service = ModelDiscoveryService(cache_ttl_seconds=3600)

    def test_cache_key_generation(self):
        k1 = self.service._cache_key("https://openrouter.ai/api/v1/")
        k2 = self.service._cache_key("https://openrouter.ai/api/v1")
        self.assertEqual(k1, k2)

    def test_cache_storage_and_retrieval(self):
        self.service._cache["https://api.openai.com/v1"] = {
            "timestamp": 9999999999,
            "models": [{"id": "gpt-4o", "name": "GPT-4o"}],
            "base_url": "https://api.openai.com/v1"
        }
        
        async def run_test():
            ok, models, err = await self.service.discover_models("https://api.openai.com/v1", "dummy-key")
            self.assertTrue(ok)
            self.assertEqual(len(models), 1)
            self.assertEqual(models[0]["id"], "gpt-4o")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
