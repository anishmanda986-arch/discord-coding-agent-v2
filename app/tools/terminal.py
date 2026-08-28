import subprocess
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, Optional
from ..security.validator import SecurityValidator
from ..security.redaction import SecretRedactor

class TerminalTools:
    """
    Executes controlled terminal commands with timeout enforcement,
    output size limits, and security validation.
    """

    def __init__(self, workspace_path: str, default_timeout_sec: int = 30):
        self.workspace_path = str(Path(workspace_path).resolve())
        self.default_timeout_sec = default_timeout_sec

    async def execute_command(self, command: str, timeout_sec: Optional[int] = None) -> Dict[str, Any]:
        is_safe, error_msg = SecurityValidator.is_safe_command(command)
        if not is_safe:
            return {
                "success": False,
                "exit_code": 126,
                "stdout": "",
                "stderr": f"Security Violation: {error_msg}",
                "duration_ms": 0
            }

        timeout = timeout_sec or self.default_timeout_sec
        start = time.time()

        loop = asyncio.get_event_loop()
        def _run():
            try:
                proc = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.workspace_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                    text=True
                )
                stdout = proc.stdout[:10000] if proc.stdout else ""
                stderr = proc.stderr[:10000] if proc.stderr else ""
                return {
                    "success": proc.returncode == 0,
                    "exit_code": proc.returncode,
                    "stdout": SecretRedactor.redact_text(stdout),
                    "stderr": SecretRedactor.redact_text(stderr),
                    "timed_out": False
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "exit_code": 124,
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds",
                    "timed_out": True
                }
            except Exception as e:
                return {
                    "success": False,
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": SecretRedactor.redact_text(str(e)),
                    "timed_out": False
                }

        res = await loop.run_in_executor(None, _run)
        res["duration_ms"] = int((time.time() - start) * 1000)
        res["command"] = SecretRedactor.redact_text(command)
        return res
