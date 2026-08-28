import unittest
import tempfile
import shutil
import time
import os
from pathlib import Path
from app.storage.cleanup import StorageCleanupWorker

class TestCleanupWorker(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.worker = StorageCleanupWorker(workspace_root=self.tmp_dir, temp_ttl_seconds=1)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_cleanup_expired_workspaces_and_zips(self):
        # Create temp expired directory
        expired_dir = Path(self.tmp_dir) / "task_expired"
        expired_dir.mkdir(parents=True, exist_ok=True)
        (expired_dir / "app.py").write_text("print('test')")

        # Create persistent directory with flag
        persistent_dir = Path(self.tmp_dir) / "task_persistent"
        persistent_dir.mkdir(parents=True, exist_ok=True)
        (persistent_dir / ".persistent").write_text("1")
        (persistent_dir / "app.py").write_text("print('save')")

        # Create expired zip
        expired_zip = Path(self.tmp_dir) / "task_old.zip"
        expired_zip.write_text("fake zip data")

        # Set mtime back in time
        old_time = time.time() - 100
        os.utime(expired_dir, (old_time, old_time))
        os.utime(persistent_dir, (old_time, old_time))
        os.utime(expired_zip, (old_time, old_time))

        report = self.worker.clean_orphaned_workspaces()
        self.assertEqual(report["deleted_workspaces"], 1)
        self.assertEqual(report["deleted_zips"], 1)

        self.assertFalse(expired_dir.exists())
        self.assertFalse(expired_zip.exists())
        self.assertTrue(persistent_dir.exists())

if __name__ == "__main__":
    unittest.main()
