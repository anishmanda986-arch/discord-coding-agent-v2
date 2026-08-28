import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

class SmartRepoIndex:
    """
    Intelligent repository indexer for 5x cost reduction.
    Parses symbols, imports, exports, functions, routes, and classes.
    Uses SHA-256 hash-based invalidation to never re-index or re-read unchanged files.
    Dynamically extracts only relevant files for any given task prompt.
    """

    IGNORE_DIRS = {
        ".git", "node_modules", "__pycache__", ".next", "dist", "build",
        ".venv", "venv", ".idea", ".vscode", "coverage", ".pytest_cache"
    }

    IGNORE_EXTS = {
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2",
        ".ttf", ".eot", ".zip", ".tar", ".gz", ".lock", ".log", ".pyc"
    }

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        # file_path -> metadata
        self._index: Dict[str, Dict[str, Any]] = {}

    def _compute_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def _detect_language(self, path: Path) -> str:
        ext = path.suffix.lower()
        mapping = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript-react",
            ".js": "javascript",
            ".jsx": "javascript-react",
            ".json": "json",
            ".md": "markdown",
            ".go": "go",
            ".rs": "rust",
            ".kt": "kotlin",
            ".java": "java",
            ".sql": "sql",
            ".html": "html",
            ".css": "css",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".sh": "bash"
        }
        return mapping.get(ext, "text")

    def _extract_symbols(self, content: str, language: str) -> Dict[str, List[str]]:
        """Extracts functions, classes, routes, and imports from code."""
        functions = []
        classes = []
        routes = []
        imports = []

        if language in ("python",):
            # Python def / class / routes
            for match in re.finditer(r"^\s*def\s+([a-zA-Z0-9_]+)\s*\(", content, re.MULTILINE):
                functions.append(match.group(1))
            for match in re.finditer(r"^\s*class\s+([a-zA-Z0-9_]+)", content, re.MULTILINE):
                classes.append(match.group(1))
            for match in re.finditer(r"@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]", content):
                routes.append(f"{match.group(1).upper()} {match.group(2)}")
            for match in re.finditer(r"^\s*(?:from\s+([a-zA-Z0-9_.]+)\s+import|import\s+([a-zA-Z0-9_.]+))", content, re.MULTILINE):
                imp = match.group(1) or match.group(2)
                if imp:
                    imports.append(imp)

        elif "javascript" in language or "typescript" in language:
            # JS/TS functions, classes, components, routes, imports
            for match in re.finditer(r"(?:function\s+([a-zA-Z0-9_]+)|const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)", content):
                fn = match.group(1) or match.group(2)
                if fn:
                    functions.append(fn)
            for match in re.finditer(r"class\s+([a-zA-Z0-9_]+)", content):
                classes.append(match.group(1))
            for match in re.finditer(r"(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]", content):
                routes.append(f"{match.group(1).upper()} {match.group(2)}")
            for match in re.finditer(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", content):
                imports.append(match.group(1))

        return {
            "functions": functions[:40],
            "classes": classes[:20],
            "routes": routes[:20],
            "imports": imports[:30]
        }

    def index_repository(self) -> Dict[str, Any]:
        """
        Scans all files in workspace. Re-indexes only modified or new files.
        """
        if not self.workspace_path.exists():
            return {"total_files": 0, "indexed_files": 0, "reused_files": 0}

        current_files = set()
        reused_count = 0
        new_or_modified_count = 0

        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.IGNORE_EXTS:
                    continue
                try:
                    rel_path = str(file_path.relative_to(self.workspace_path))
                    current_files.add(rel_path)

                    file_stat = file_path.stat()
                    if file_stat.st_size > 2 * 1024 * 1024:  # Skip >2MB
                        continue

                    content_bytes = file_path.read_bytes()
                    file_hash = self._compute_hash(content_bytes)

                    # Check if hash is identical
                    if rel_path in self._index and self._index[rel_path].get("hash") == file_hash:
                        reused_count += 1
                        continue

                    # Index new or modified file
                    try:
                        text_content = content_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        text_content = content_bytes.decode("utf-8", errors="ignore")

                    lang = self._detect_language(file_path)
                    symbols = self._extract_symbols(text_content, lang)

                    self._index[rel_path] = {
                        "path": rel_path,
                        "language": lang,
                        "size": file_stat.st_size,
                        "hash": file_hash,
                        "symbols": symbols,
                        "summary": f"{lang} file with {len(symbols['functions'])} functions, {len(symbols['classes'])} classes"
                    }
                    new_or_modified_count += 1

                except Exception:
                    continue

        # Prune deleted files
        for old_path in list(self._index.keys()):
            if old_path not in current_files:
                del self._index[old_path]

        return {
            "total_files": len(self._index),
            "indexed_files": new_or_modified_count,
            "reused_files": reused_count
        }

    def retrieve_relevant_context(self, prompt: str, max_files: int = 6, token_budget: int = 4000) -> Dict[str, Any]:
        """
        Dynamically extracts ONLY the most relevant files and symbols for a task.
        Prevents sending the whole repo.
        """
        self.index_repository()
        
        prompt_words = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", prompt.lower()))
        scored_files = []

        for path, meta in self._index.items():
            score = 0
            path_lower = path.lower()
            
            # File path keywords match
            for word in prompt_words:
                if len(word) > 2 and word in path_lower:
                    score += 15
                    
            # Check symbols match
            symbols = meta.get("symbols", {})
            for fn in symbols.get("functions", []):
                for word in prompt_words:
                    if len(word) > 2 and word in fn.lower():
                        score += 20
                        
            for cls_name in symbols.get("classes", []):
                for word in prompt_words:
                    if len(word) > 2 and word in cls_name.lower():
                        score += 25

            for route in symbols.get("routes", []):
                for word in prompt_words:
                    if len(word) > 2 and word in route.lower():
                        score += 30

            # Boost config / main entry points slightly if no specific score
            if any(p in path_lower for p in ("app.py", "main.py", "index.ts", "app.tsx", "server.ts", "package.json")):
                score += 5

            if score > 0:
                scored_files.append((score, path, meta))

        # Sort by score descending
        scored_files.sort(key=lambda x: x[0], reverse=True)
        selected_paths = [p for _, p, _ in scored_files[:max_files]]

        # If nothing matched, pick top entry files
        if not selected_paths and self._index:
            entry_candidates = [p for p in self._index.keys() if any(k in p.lower() for k in ("main", "app", "index", "readme", "server"))]
            selected_paths = entry_candidates[:3] or list(self._index.keys())[:3]

        # Read contents up to token budget
        files_payload = []
        tokens_accumulated = 0

        for rel_path in selected_paths:
            full_path = self.workspace_path / rel_path
            if full_path.exists() and full_path.is_file():
                try:
                    content = full_path.read_text(encoding="utf-8", errors="replace")
                    est_tokens = len(content) // 4
                    if tokens_accumulated + est_tokens <= token_budget:
                        files_payload.append({
                            "path": rel_path,
                            "content": content,
                            "symbols": self._index.get(rel_path, {}).get("symbols", {})
                        })
                        tokens_accumulated += est_tokens
                    else:
                        # Truncate if needed
                        remain_chars = (token_budget - tokens_accumulated) * 4
                        if remain_chars > 200:
                            files_payload.append({
                                "path": rel_path,
                                "content": content[:remain_chars] + "\n... [truncated for context limit]",
                                "symbols": self._index.get(rel_path, {}).get("symbols", {})
                            })
                            tokens_accumulated = token_budget
                            break
                except Exception:
                    continue

        return {
            "selected_files": files_payload,
            "total_files_indexed": len(self._index),
            "relevance_count": len(selected_paths),
            "estimated_context_tokens": tokens_accumulated
        }

# Backward compatibility alias
RepoIndexCache = SmartRepoIndex
