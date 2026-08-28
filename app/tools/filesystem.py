import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from ..security.validator import SecurityValidator
from .safety import FileSafetyValidator, TaskBackupStore
from .patcher import DiffPatcher

class FileSystemTools:
    """
    Production-Grade Secure & Atomic FileSystem Tools.
    
    Guarantees:
      - Atomic File Writes via target_file.agent_tmp + fsync + atomic rename (os.replace)
      - Pre-modification snapshots and automatic instant rollback on any verification failure
      - Zero corrupted, blank, or unexpectedly truncated files
      - Pre-commit syntax validation (Python AST, JSON, JS/TS, YAML)
      - SHA-256 Checksums tracked across before & after states
      - Absolute workspace jailing to prevent path traversal
    """

    def __init__(self, workspace_path: str, max_file_bytes: int = 5 * 1024 * 1024):
        self.workspace_path = str(Path(workspace_path).resolve())
        self.max_file_bytes = max_file_bytes
        self.backups = TaskBackupStore(self.workspace_path)
        self.activity_log: List[Dict[str, Any]] = []
        Path(self.workspace_path).mkdir(parents=True, exist_ok=True)

    def _resolve(self, rel_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        return SecurityValidator.validate_workspace_path(self.workspace_path, rel_path)

    def read_file(self, rel_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict[str, Any]:
        valid, resolved, err = self._resolve(rel_path)
        if not valid:
            return {"success": False, "error": err}

        path_obj = Path(resolved)
        if not path_obj.exists() or not path_obj.is_file():
            return {"success": False, "error": f"File not found: {rel_path}"}

        size = path_obj.stat().st_size
        if size > self.max_file_bytes:
            return {"success": False, "error": f"File exceeds size limit ({size} > {self.max_file_bytes} bytes)."}

        try:
            content = path_obj.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines(keepends=True)
            total_lines = len(lines)
            sha256 = FileSafetyValidator.compute_sha256(content)

            if start_line is not None or end_line is not None:
                s = max(1, start_line or 1) - 1
                e = min(total_lines, end_line or total_lines)
                sliced_content = "".join(lines[s:e])
                return {
                    "success": True,
                    "path": rel_path,
                    "content": sliced_content,
                    "total_lines": total_lines,
                    "start_line": s + 1,
                    "end_line": e,
                    "sha256": sha256,
                    "size_bytes": size
                }

            return {
                "success": True,
                "path": rel_path,
                "content": content,
                "total_lines": total_lines,
                "sha256": sha256,
                "size_bytes": size
            }
        except Exception as e:
            return {"success": False, "error": f"Read error: {str(e)}"}

    def _atomic_write_verified(self, rel_path: str, new_content: str, old_content: Optional[str] = None, is_delete: bool = False) -> Dict[str, Any]:
        """
        Core atomic write workflow with safety checks and automatic rollback:
          1. Snapshot backup
          2. Size & anti-truncation validation
          3. Syntax check
          4. Write to .agent_tmp with fsync
          5. Verify temp file bytes & encoding
          6. Atomic os.replace
          7. Read-back & SHA-256 check
          8. Log activity
        """
        valid, resolved, err = self._resolve(rel_path)
        if not valid:
            return {"success": False, "error": err}

        target_path = Path(resolved)
        temp_path = target_path.parent / f"{target_path.name}.agent_tmp"

        # 1. Snapshot backup
        self.backups.create_snapshot(rel_path)
        old_hash = FileSafetyValidator.compute_sha256(old_content) if old_content is not None else None
        size_before = len(old_content.encode("utf-8")) if old_content is not None else 0

        # 2. File size & unexpected truncation validation
        size_ok, size_err = FileSafetyValidator.validate_file_size_and_truncation(
            rel_path=rel_path,
            old_content=old_content,
            new_content=new_content,
            is_explicit_delete=is_delete
        )
        if not size_ok:
            self.backups.rollback(rel_path)
            return {"success": False, "error": f"Safety check failed: {size_err}", "rolled_back": True}

        # 3. Syntax validation
        syntax_ok, syntax_err = FileSafetyValidator.validate_syntax(rel_path, new_content)
        if not syntax_ok:
            self.backups.rollback(rel_path)
            return {"success": False, "error": f"Syntax validation failed: {syntax_err}", "rolled_back": True}

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 4. Write to temp file & fsync
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(new_content)
                f.flush()
                os.fsync(f.fileno())

            # 5. Verify temp file
            if not temp_path.exists():
                raise IOError(f"Temp file '{temp_path}' was not created.")
            temp_size = temp_path.stat().st_size
            expected_bytes = len(new_content.encode("utf-8"))
            if temp_size != expected_bytes:
                raise IOError(f"Temp file size mismatch ({temp_size} != {expected_bytes} bytes).")

            # 6. Atomic replacement
            os.replace(temp_path, target_path)

            # 7. Read-back & verify hash
            disk_content = target_path.read_text(encoding="utf-8")
            new_hash = FileSafetyValidator.compute_sha256(disk_content)
            size_after = len(disk_content.encode("utf-8"))

            if new_hash != FileSafetyValidator.compute_sha256(new_content):
                raise IOError("SHA-256 verification failed after disk write.")

            # 8. Record file activity
            action_type = "ADDED" if old_content is None else "MODIFIED"
            diff_data = DiffPatcher.extract_diff_summary(DiffPatcher.generate_unified_diff(old_content or "", new_content, rel_path))
            
            activity = {
                "action": action_type,
                "path": rel_path,
                "old_hash": old_hash,
                "new_hash": new_hash,
                "size_before": size_before,
                "size_after": size_after,
                "additions": diff_data["additions"],
                "deletions": diff_data["deletions"]
            }
            self.activity_log.append(activity)

            return {
                "success": True,
                "path": rel_path,
                "action": action_type,
                "bytes_written": size_after,
                "sha256": new_hash,
                "size_before": size_before,
                "size_after": size_after,
                "message": f"Successfully and atomically wrote '{rel_path}'."
            }

        except Exception as e:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            # Rollback original file
            self.backups.rollback(rel_path)
            return {
                "success": False,
                "error": f"Atomic write failed: {str(e)}. Original file restored.",
                "rolled_back": True
            }

    def write_file(self, rel_path: str, content: str) -> Dict[str, Any]:
        """Atomically creates or overwrites a file."""
        valid, resolved, err = self._resolve(rel_path)
        if not valid:
            return {"success": False, "error": err}

        target_path = Path(resolved)
        old_content = None
        if target_path.exists() and target_path.is_file():
            try:
                old_content = target_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                old_content = None

        return self._atomic_write_verified(rel_path, content, old_content=old_content)

    def edit_file(self, rel_path: str, target_content: str, replacement_content: str) -> Dict[str, Any]:
        """Surgically replaces target_content with replacement_content."""
        valid, resolved, err = self._resolve(rel_path)
        if not valid:
            return {"success": False, "error": err}

        target_path = Path(resolved)
        if not target_path.exists() or not target_path.is_file():
            return {"success": False, "error": f"File does not exist: {rel_path}"}

        try:
            current = target_path.read_text(encoding="utf-8", errors="replace")
            if target_content not in current:
                return {
                    "success": False,
                    "error": f"Target content not found in {rel_path}. Make sure the target text matches exactly."
                }

            count = current.count(target_content)
            if count > 1:
                return {
                    "success": False,
                    "error": f"Target content is ambiguous (found {count} occurrences in {rel_path}). Provide more surrounding context lines."
                }

            updated = current.replace(target_content, replacement_content, 1)
            return self._atomic_write_verified(rel_path, updated, old_content=current)
        except Exception as e:
            return {"success": False, "error": f"Edit error: {str(e)}"}

    def patch_file(self, rel_path: str, patch_type: str, **kwargs) -> Dict[str, Any]:
        """
        Applies patch-first modifications (replace_range, insert, delete_range, replace_function).
        """
        valid, resolved, err = self._resolve(rel_path)
        if not valid:
            return {"success": False, "error": err}

        target_path = Path(resolved)
        if not target_path.exists() or not target_path.is_file():
            return {"success": False, "error": f"File does not exist: {rel_path}"}

        current = target_path.read_text(encoding="utf-8", errors="replace")
        ok = False
        new_text = current
        msg = None

        if patch_type == "replace_range":
            ok, new_text, msg = DiffPatcher.replace_range(
                current, kwargs.get("start_line", 1), kwargs.get("end_line", 1), kwargs.get("replacement_text", "")
            )
        elif patch_type == "insert":
            ok, new_text, msg = DiffPatcher.insert_at_line(
                current, kwargs.get("line_number", 1), kwargs.get("content", "")
            )
        elif patch_type == "delete_range":
            ok, new_text, msg = DiffPatcher.delete_range(
                current, kwargs.get("start_line", 1), kwargs.get("end_line", 1)
            )
        elif patch_type == "replace_function":
            ok, new_text, msg = DiffPatcher.replace_function(
                current, kwargs.get("function_name", ""), kwargs.get("new_function_code", "")
            )
        elif patch_type == "unified_diff":
            ok, new_text, msg = DiffPatcher.apply_unified_patch(current, kwargs.get("diff_text", ""))
        else:
            return {"success": False, "error": f"Unknown patch type: {patch_type}"}

        if not ok:
            return {"success": False, "error": msg or "Patch application failed"}

        return self._atomic_write_verified(rel_path, new_text, old_content=current)

    def delete_file(self, rel_path: str) -> Dict[str, Any]:
        valid, resolved, err = self._resolve(rel_path)
        if not valid:
            return {"success": False, "error": err}

        target_path = Path(resolved)
        if not target_path.exists():
            return {"success": False, "error": f"Target does not exist: {rel_path}"}

        try:
            self.backups.create_snapshot(rel_path)
            if target_path.is_file() or target_path.is_symlink():
                target_path.unlink()
            elif target_path.is_dir():
                shutil.rmtree(target_path)

            self.activity_log.append({
                "action": "REMOVED",
                "path": rel_path,
                "old_hash": None,
                "new_hash": None
            })
            return {"success": True, "path": rel_path, "message": f"Deleted {rel_path}"}
        except Exception as e:
            return {"success": False, "error": f"Delete error: {str(e)}"}

    def rollback_task(self) -> List[str]:
        """Rolls back all files modified in this workspace instance."""
        return self.backups.rollback_all()

    def list_tree(self, rel_dir: str = ".", max_depth: int = 4) -> Dict[str, Any]:
        valid, resolved, err = self._resolve(rel_dir)
        if not valid:
            return {"success": False, "error": err}

        base_dir = Path(resolved)
        if not base_dir.exists():
            return {"success": False, "error": f"Directory not found: {rel_dir}"}

        tree_items = []
        ignore = {".git", "node_modules", "__pycache__", "dist", "build", ".venv", "venv", ".agent_backups"}

        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in ignore]
            cur_path = Path(root)
            depth = len(cur_path.relative_to(base_dir).parts)
            if depth > max_depth:
                continue

            for d in dirs:
                rel = str((cur_path / d).relative_to(Path(self.workspace_path)))
                tree_items.append({"path": rel, "type": "directory"})

            for f in files:
                if f.endswith(".agent_tmp"):
                    continue
                rel = str((cur_path / f).relative_to(Path(self.workspace_path)))
                size = (cur_path / f).stat().st_size
                tree_items.append({"path": rel, "type": "file", "size": size})

        return {"success": True, "items": tree_items[:200], "total_count": len(tree_items)}

    def batch_read(self, paths: List[str]) -> Dict[str, Any]:
        results = {}
        for p in paths:
            results[p] = self.read_file(p)
        return {"success": True, "results": results}

    def batch_write(self, files: Dict[str, str]) -> Dict[str, Any]:
        results = {}
        for p, content in files.items():
            results[p] = self.write_file(p, content)
        return {"success": True, "results": results}
