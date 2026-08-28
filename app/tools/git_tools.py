import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from ..security.redaction import SecretRedactor

class GitTools:
    """
    Manages local Git workflow for Coding Agent tasks.
    Supports init, checkout branch, diff, status, add, commit.
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = str(Path(workspace_path).resolve())

    async def _run_git(self, args: list) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        def _exec():
            try:
                proc = subprocess.run(
                    ["git"] + args,
                    cwd=self.workspace_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=20,
                    text=True
                )
                return {
                    "success": proc.returncode == 0,
                    "stdout": SecretRedactor.redact_text(proc.stdout or ""),
                    "stderr": SecretRedactor.redact_text(proc.stderr or ""),
                    "exit_code": proc.returncode
                }
            except Exception as e:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": SecretRedactor.redact_text(str(e)),
                    "exit_code": 1
                }
        return await loop.run_in_executor(None, _exec)

    async def init_repo(self) -> Dict[str, Any]:
        return await self._run_git(["init"])

    async def create_branch(self, branch_name: str) -> Dict[str, Any]:
        return await self._run_git(["checkout", "-b", branch_name])

    async def get_status(self) -> Dict[str, Any]:
        return await self._run_git(["status", "--short"])

    async def get_diff(self) -> Dict[str, Any]:
        return await self._run_git(["diff"])

    async def commit_all(self, message: str) -> Dict[str, Any]:
        add_res = await self._run_git(["add", "."])
        if not add_res["success"]:
            return add_res
        return await self._run_git(["commit", "-m", message])
