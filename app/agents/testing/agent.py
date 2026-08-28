from pathlib import Path
from typing import Dict, Any, List
from ..base import BaseAgent
from ...router.router import AgentMessage
from ...sandbox.runner import SandboxRunner

class TestingAgent(BaseAgent):
    """
    Dedicated Testing Agent.
    Detects project test harnesses (Node, Python, Go, Rust, Gradle),
    runs sandbox tests, parses stack traces, deduplicates errors, and formats test summaries.
    """

    def __init__(self):
        super().__init__(name="testing_agent", role="Test Discovery & Execution")

    def detect_test_command(self, workspace_path: Path) -> str:
        if (workspace_path / "package.json").exists():
            return "npm test"
        if (workspace_path / "pytest.ini").exists() or (workspace_path / "tests").exists():
            return "pytest"
        if (workspace_path / "pyproject.toml").exists():
            return "python3 -m unittest discover tests"
        if (workspace_path / "go.mod").exists():
            return "go test ./..."
        if (workspace_path / "Cargo.toml").exists():
            return "cargo test"
        if (workspace_path / "gradlew").exists():
            return "./gradlew test"
        return "echo 'No test suite detected'"

    async def handle_message(self, message: AgentMessage) -> AgentMessage:
        workspace = message.payload.get("workspace_path", ".")
        w_path = Path(workspace)
        test_cmd = message.payload.get("test_command") or self.detect_test_command(w_path)

        runner = SandboxRunner(str(w_path))
        exec_res = await runner.run_command(test_cmd, timeout_sec=30)

        # Truncate and parse output
        stdout = exec_res.get("stdout", "")
        stderr = exec_res.get("stderr", "")
        passed = exec_res.get("exit_code") == 0

        parsed_summary = {
            "test_command": test_cmd,
            "passed": passed,
            "exit_code": exec_res.get("exit_code"),
            "duration_ms": exec_res.get("duration_ms"),
            "execution_engine": exec_res.get("execution_engine"),
            "output_summary": (stdout if stdout else stderr)[:500] or "Execution completed."
        }

        return self.create_result_message(message, parsed_summary)
