import unittest
import tempfile
import shutil
import asyncio
from pathlib import Path
from app.tools.filesystem import FileSystemTools
from app.tools.patcher import DiffPatcher
from app.tools.search import SearchTools

class TestToolsAndDiffs(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.fs = FileSystemTools(self.tmp_dir)
        self.search = SearchTools(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_filesystem_write_read_edit_delete(self):
        # Write
        w_res = self.fs.write_file("src/app.py", "def start():\n    return 'v1'\n")
        self.assertTrue(w_res["success"])

        # Read
        r_res = self.fs.read_file("src/app.py")
        self.assertTrue(r_res["success"])
        self.assertIn("v1", r_res["content"])

        # Edit surgical
        e_res = self.fs.edit_file("src/app.py", "return 'v1'", "return 'v2'")
        self.assertTrue(e_res["success"])
        self.assertIn("v2", self.fs.read_file("src/app.py")["content"])

        # Delete
        d_res = self.fs.delete_file("src/app.py")
        self.assertTrue(d_res["success"])
        self.assertFalse(self.fs.read_file("src/app.py")["success"])

    def test_diff_patcher_token_savings(self):
        orig = "def hello():\n    print('hello world')\n    return True\n"
        new = "def hello():\n    print('hello production')\n    return True\n"

        ctx = DiffPatcher.make_diff_context("hello.py", orig, new)
        self.assertIn("hello production", ctx["diff"])
        self.assertEqual(ctx["additions"], 1)
        self.assertEqual(ctx["deletions"], 1)
        self.assertGreaterEqual(ctx["token_savings_pct"], 0.0)

    def test_grep_search(self):
        self.fs.write_file("config.py", "DATABASE_URL = 'sqlite:///app.db'\n")
        res = self.search.grep_search("DATABASE_URL")
        self.assertTrue(res["success"])
        self.assertEqual(res["match_count"], 1)
        self.assertEqual(res["matches"][0]["file"], "config.py")

if __name__ == "__main__":
    unittest.main()
