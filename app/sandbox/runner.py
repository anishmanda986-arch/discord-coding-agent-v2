import subprocess
import asyncio
import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from .security import SandboxSecurityPolicy
from ..security.validator import SecurityValidator
from ..security.redaction import SecretRedactor

class SandboxRunner:
    """
    Sandboxed Execution Runner.
    Executes project tests and builds in an isolated environment.
    Automatically detects Docker if available; falls back to an isolated
    process runner with timeouts and directory sandboxing.
    """

    def __init__(self, workspace_path: str, prefer_docker: bool = False):
        self.workspace_path = str(Path(workspace_path).resolve())
        self.prefer_docker = prefer_docker and (shutil.which("docker") is not None)

    async def run_command(self, command: str, timeout_sec: int = 45) -> Dict[str, Any]:
        is_safe, error_msg = SecurityValidator.is_safe_command(command)
        if not is_safe:
            return {
                "success": False,
                "exit_code": 126,
                "stdout": "",
                "stderr": f"Sandbox Security Rejection: {error_msg}",
                "execution_engine": "security-filter",
                "duration_ms": 0
            }

        start = time.time()

        if self.prefer_docker:
            return await self._run_in_docker(command, timeout_sec, start)
        else:
            return await self._run_isolated_subprocess(command, timeout_sec, start)

    async def _run_in_docker(self, command: str, timeout_sec: int, start_time: float) -> Dict[str, Any]:
        flags = SandboxSecurityPolicy.get_docker_run_flags(self.workspace_path)
        docker_cmd = ["docker", "run"] + flags + ["alpine:latest", "sh", "-c", command]
        
        loop = asyncio.get_event_loop()
        def _exec():
            try:
                proc = subprocess.run(
                    docker_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout_sec,
                    text=True
                )
                return {
                    "success": proc.returncode == 0,
                    "exit_code": proc.returncode,
                    "stdout": SecretRedactor.redact_text(proc.stdout[:8000] or ""),
                    "stderr": SecretRedactor.redact_text(proc.stderr[:8000] or ""),
                    "execution_engine": "docker-sandbox"
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "exit_code": 124,
                    "stdout": "",
                    "stderr": f"Execution timed out in Docker sandbox after {timeout_sec}s",
                    "execution_engine": "docker-sandbox"
                }
            except Exception as e:
                return {
                    "success": False,
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": f"Docker error: {str(e)}",
                    "execution_engine": "docker-sandbox"
                }

        res = await loop.run_in_executor(None, _exec)
        res["duration_ms"] = int((time.time() - start_time) * 1000)
        return res

    async def _run_isolated_subprocess(self, command: str, timeout_sec: int, start_time: float) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        def _exec():
            try:
                proc = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.workspace_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout_sec,
                    text=True
                )
                return {
                    "success": proc.returncode == 0,
                    "exit_code": proc.returncode,
                    "stdout": SecretRedactor.redact_text(proc.stdout[:8000] or ""),
                    "stderr": SecretRedactor.redact_text(proc.stderr[:8000] or ""),
                    "execution_engine": "process-sandbox"
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "exit_code": 124,
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout_sec}s",
                    "execution_engine": "process-sandbox"
                }
            except Exception as e:
                return {
                    "success": False,
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": SecretRedactor.redact_text(str(e)),
                    "execution_engine": "process-sandbox"
                }

        res = await loop.run_in_executor(None, _exec)
        res["duration_ms"] = int((time.time() - start_time) * 1000)
        return res
