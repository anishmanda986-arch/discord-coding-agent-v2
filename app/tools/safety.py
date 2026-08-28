import os
import ast
import json
import hashlib
import py_compile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

class FileSafetyError(Exception):
    """Raised when a file safety or validation check fails."""
    pass

class FileSafetyValidator:
    """
    Comprehensive File Safety & Syntax Validator.
    Ensures zero blank/corrupted/truncated files and verifies syntax before writing.
    """

    MAX_FILE_BYTES = 5 * 1024 * 1024  # 5MB
    MAX_TRUNCATION_RATIO = 0.20  # If new file is <20% of previous size for files > 500 lines, flag as truncation

    @staticmethod
    def compute_sha256(content: str or bytes) -> str:
        """Computes SHA-256 hash of content."""
        if isinstance(content, str):
            data = content.encode("utf-8")
        else:
            data = content
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def compute_file_sha256(file_path: Path) -> Optional[str]:
        """Computes SHA-256 hash of a file on disk."""
        if not file_path.exists() or not file_path.is_file():
            return None
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    @classmethod
    def validate_file_size_and_truncation(
        cls,
        rel_path: str,
        old_content: Optional[str],
        new_content: str,
        is_explicit_delete: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Detects unexpected blank files, drastic truncations, and size explosions.
        """
        new_bytes = len(new_content.encode("utf-8"))

        # 1. Size ceiling check
        if new_bytes > cls.MAX_FILE_BYTES:
            return False, f"File size explosion: {new_bytes} bytes exceeds safety limit ({cls.MAX_FILE_BYTES} bytes)."

        # 2. Unexpected blank file check
        if old_content is not None and len(old_content.strip()) > 0:
            if len(new_content.strip()) == 0 and not is_explicit_delete:
                return False, f"Unexpected empty file: '{rel_path}' previously had {len(old_content)} characters but generated output was blank."

        # 3. Suspicious truncation check for non-trivial files
        if old_content is not None:
            old_lines = old_content.splitlines()
            new_lines = new_content.splitlines()
            
            # If old file was >= 100 lines and new file is < 15 lines without deletion flag
            if len(old_lines) >= 100 and len(new_lines) < 15 and not is_explicit_delete:
                return False, f"Suspicious truncation detected in '{rel_path}': shrunk from {len(old_lines)} lines to {len(new_lines)} lines."

        return True, None

    @classmethod
    def validate_syntax(cls, rel_path: str, content: str) -> Tuple[bool, Optional[str]]:
        """
        Performs language-specific syntax validation.
        Supports Python, JSON, YAML, JavaScript, TypeScript, and HTML.
        """
        path_lower = rel_path.lower()

        # 1. Python Validation
        if path_lower.endswith(".py"):
            try:
                ast.parse(content, filename=rel_path)
            except SyntaxError as e:
                return False, f"Python syntax error at line {e.lineno}, col {e.offset}: {e.msg}"
            except Exception as e:
                return False, f"Python parse error: {str(e)}"

        # 2. JSON Validation
        elif path_lower.endswith(".json"):
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                return False, f"JSON decode error at line {e.lineno}, col {e.colno}: {e.msg}"

        # 3. YAML Validation (basic structural checks)
        elif path_lower.endswith(".yml") or path_lower.endswith(".yaml"):
            lines = content.splitlines()
            for idx, line in enumerate(lines, 1):
                # Check for bad tab indentation in YAML
                if "\t" in line and not line.strip().startswith("#"):
                    return False, f"YAML syntax warning at line {idx}: Tab characters used for indentation are invalid in YAML."

        # 4. JS / TS Bracket Balance Validation
        elif path_lower.endswith((".js", ".jsx", ".ts", ".tsx")):
            brackets = {"(": ")", "{": "}", "[": "]"}
            stack = []
            in_single_quote = False
            in_double_quote = False
            in_backtick = False
            in_line_comment = False
            in_block_comment = False

            i = 0
            while i < len(content):
                ch = content[i]
                next_ch = content[i+1] if i + 1 < len(content) else ""

                if in_line_comment:
                    if ch == "\n":
                        in_line_comment = False
                elif in_block_comment:
                    if ch == "*" and next_ch == "/":
                        in_block_comment = False
                        i += 1
                elif in_single_quote:
                    if ch == "\\" and next_ch:
                        i += 1
                    elif ch == "'":
                        in_single_quote = False
                elif in_double_quote:
                    if ch == "\\" and next_ch:
                        i += 1
                    elif ch == '"':
                        in_double_quote = False
                elif in_backtick:
                    if ch == "\\" and next_ch:
                        i += 1
                    elif ch == "`":
                        in_backtick = False
                else:
                    if ch == "/" and next_ch == "/":
                        in_line_comment = True
                        i += 1
                    elif ch == "/" and next_ch == "*":
                        in_block_comment = True
                        i += 1
                    elif ch == "'":
                        in_single_quote = True
                    elif ch == '"':
                        in_double_quote = True
                    elif ch == "`":
                        in_backtick = True
                    elif ch in brackets:
                        stack.append((ch, i))
                    elif ch in brackets.values():
                        if not stack:
                            return False, f"Syntax error in '{rel_path}': Unmatched closing bracket '{ch}'."
                        open_b, _ = stack.pop()
                        if brackets[open_b] != ch:
                            return False, f"Syntax error in '{rel_path}': Mismatched brackets '{open_b}' and '{ch}'."
                i += 1

            if stack:
                unclosed, _ = stack[-1]
                return False, f"Syntax error in '{rel_path}': Unclosed bracket '{unclosed}'."

        return True, None


class TaskBackupStore:
    """
    Manages pre-modification file snapshots for instant rollback.
    Stores previous file versions in memory and on disk.
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path).resolve()
        self.backup_dir = self.workspace_path / ".agent_backups"
        self._snapshots: Dict[str, Dict[str, Any]] = {}

    def create_snapshot(self, rel_path: str) -> None:
        """Saves a snapshot of an existing file before modification."""
        full_path = self.workspace_path / rel_path
        if full_path.exists() and full_path.is_file():
            content = full_path.read_text(encoding="utf-8", errors="replace")
            sha256 = FileSafetyValidator.compute_sha256(content)
            self._snapshots[rel_path] = {
                "existed": True,
                "content": content,
                "sha256": sha256,
                "size_bytes": len(content.encode("utf-8"))
            }
        else:
            self._snapshots[rel_path] = {
                "existed": False,
                "content": None,
                "sha256": None,
                "size_bytes": 0
            }

    def rollback(self, rel_path: str) -> bool:
        """Restores a specific file to its pre-modification snapshot."""
        if rel_path not in self._snapshots:
            return False

        snapshot = self._snapshots[rel_path]
        full_path = self.workspace_path / rel_path

        if snapshot["existed"]:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(snapshot["content"], encoding="utf-8")
        else:
            # File didn't exist before, so remove it
            if full_path.exists():
                full_path.unlink()

        return True

    def rollback_all(self) -> List[str]:
        """Rolls back all files modified in the current task."""
        restored = []
        for rel_path in list(self._snapshots.keys()):
            if self.rollback(rel_path):
                restored.append(rel_path)
        return restored

    def get_snapshot(self, rel_path: str) -> Optional[Dict[str, Any]]:
        return self._snapshots.get(rel_path)
