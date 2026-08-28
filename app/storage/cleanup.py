import os
import shutil
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from ..security.validator import SecurityValidator

class StorageCleanupWorker:
    """
    Automated background cleanup worker that prevents disk bloat:
      - Deletes disposable temporary workspaces exceeding TTL (default 1 hour)
      - Deletes delivered ZIP artifacts after configured TTL
      - Leaves PERSISTENT projects intact
      - Logs cleanup metrics
    """

    def __init__(self, workspace_root: str = "/tmp/coding_agent_workspaces", temp_ttl_seconds: int = 3600):
        self.workspace_root = Path(workspace_root)
        self.temp_ttl_seconds = temp_ttl_seconds
        self.is_running = False

    def clean_orphaned_workspaces(self, db_conn=None) -> Dict[str, Any]:
        now = time.time()
        deleted_workspaces = 0
        deleted_zips = 0
        freed_bytes = 0

        if not self.workspace_root.exists():
            return {"deleted_workspaces": 0, "deleted_zips": 0, "freed_bytes": 0}

        for item in self.workspace_root.iterdir():
            try:
                # Check ZIP deliverables
                if item.is_file() and item.suffix == ".zip":
                    age = now - item.stat().st_mtime
                    if age > self.temp_ttl_seconds:
                        size = item.stat().st_size
                        item.unlink()
                        deleted_zips += 1
                        freed_bytes += size

                # Check workspace directories
                elif item.is_dir():
                    # If marked persistent (e.g. .persistent flag file exists), skip
                    persistent_flag = item / ".persistent"
                    if persistent_flag.exists():
                        continue

                    age = now - item.stat().st_mtime
                    if age > self.temp_ttl_seconds:
                        dir_size = sum(f.stat().st_size for f in item.glob('**/*') if f.is_file())
                        shutil.rmtree(item, ignore_errors=True)
                        deleted_workspaces += 1
                        freed_bytes += dir_size

            except Exception:
                continue

        return {
            "deleted_workspaces": deleted_workspaces,
            "deleted_zips": deleted_zips,
            "freed_bytes": freed_bytes,
            "timestamp": now
        }

    async def start_periodic_loop(self, interval_seconds: int = 600):
        self.is_running = True
        while self.is_running:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.clean_orphaned_workspaces)
            except Exception:
                pass
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self.is_running = False
