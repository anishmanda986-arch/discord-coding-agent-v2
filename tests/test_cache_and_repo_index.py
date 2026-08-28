import unittest
import tempfile
import shutil
from pathlib import Path
from app.cache.memory import L1MemoryCache
from app.cache.repo_index import SmartRepoIndex
from app.cache.deduplication import RequestDeduplicator

class TestCacheAndRepoIndex(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_l1_cache_hit_miss_and_stats(self):
        cache = L1MemoryCache(max_items=3, default_ttl_sec=10)
        cache.set("k1", "v1")
        cache.set("k2", "v2")

        self.assertEqual(cache.get("k1"), "v1")
        self.assertIsNone(cache.get("k99"))

        stats = cache.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate_pct"], 50.0)

    def test_smart_repo_index_hash_invalidation(self):
        # Create files
        auth_file = self.workspace / "auth.py"
        auth_file.write_text("class AuthService:\n    def login(self, u, p):\n        pass\n")

        db_file = self.workspace / "db.py"
        db_file.write_text("def get_db():\n    return None\n")

        index = SmartRepoIndex(str(self.workspace))
        
        # 1st index
        res1 = index.index_repository()
        self.assertEqual(res1["indexed_files"], 2)
        self.assertEqual(res1["reused_files"], 0)

        # 2nd index without file edits -> should reuse hashes
        res2 = index.index_repository()
        self.assertEqual(res2["indexed_files"], 0)
        self.assertEqual(res2["reused_files"], 2)

        # Context retrieval extracts only relevant file
        context = index.retrieve_relevant_context("Fix login AuthService", max_files=2)
        self.assertTrue(any(f["path"] == "auth.py" for f in context["selected_files"]))

    def test_request_deduplication(self):
        dedup = RequestDeduplicator()
        h1 = dedup.compute_hash("openrouter", "gpt-4o", [{"role": "user", "content": "hello"}])
        h2 = dedup.compute_hash("openrouter", "gpt-4o", [{"role": "user", "content": "hello"}])
        self.assertEqual(h1, h2)

        dedup.store_result(h1, {"choices": [{"message": {"content": "world"}}]})
        cached = dedup.get_cached_result(h1)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["choices"][0]["message"]["content"], "world")

if __name__ == "__main__":
    unittest.main()
