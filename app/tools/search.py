import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..security.validator import SecurityValidator

class SearchTools:
    """
    Parallel file and symbol searcher with regex support and token budgeting.
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path).resolve()
        self.ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}

    def grep_search(self, query: str, file_pattern: Optional[str] = None, max_results: int = 30) -> Dict[str, Any]:
        if not self.workspace_path.exists():
            return {"success": False, "error": "Workspace directory not found"}

        try:
            pattern = re.compile(query, re.IGNORECASE)
        except Exception as e:
            return {"success": False, "error": f"Invalid regex pattern: {str(e)}"}

        matches = []
        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            for file in files:
                if file_pattern and not re.search(file_pattern, file):
                    continue

                file_path = Path(root) / file
                if file_path.stat().st_size > 1024 * 1024:
                    continue

                try:
                    rel_path = str(file_path.relative_to(self.workspace_path))
                    lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for idx, line in enumerate(lines):
                        if pattern.search(line):
                            matches.append({
                                "file": rel_path,
                                "line_number": idx + 1,
                                "content": line.strip()[:180]
                            })
                            if len(matches) >= max_results:
                                break
                except Exception:
                    continue
            if len(matches) >= max_results:
                break

        return {
            "success": True,
            "query": query,
            "match_count": len(matches),
            "matches": matches
        }

    def find_files(self, name_pattern: str, max_results: int = 50) -> Dict[str, Any]:
        if not self.workspace_path.exists():
            return {"success": False, "error": "Workspace not found"}

        matched_paths = []
        try:
            pattern = re.compile(name_pattern, re.IGNORECASE)
        except Exception:
            pattern = re.compile(re.escape(name_pattern), re.IGNORECASE)

        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            for file in files:
                rel = str((Path(root) / file).relative_to(self.workspace_path))
                if pattern.search(rel) or pattern.search(file):
                    matched_paths.append(rel)
                    if len(matched_paths) >= max_results:
                        break

        return {"success": True, "files": matched_paths}
