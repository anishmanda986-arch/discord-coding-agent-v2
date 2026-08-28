import re
import difflib
from typing import Dict, Any, List, Optional, Tuple
from .safety import FileSafetyValidator

class DiffPatcher:
    """
    Diff-First Context & File Patcher Engine.
    Provides targeted section editing (functions, classes, line ranges, unified diffs)
    to eliminate unnecessary full-file regenerations and save tokens.
    """

    @staticmethod
    def generate_unified_diff(original_text: str, new_text: str, filename: str = "file") -> str:
        orig_lines = original_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            orig_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            n=3
        )
        return "".join(diff)

    @staticmethod
    def extract_diff_summary(diff_text: str) -> Dict[str, Any]:
        additions = 0
        deletions = 0
        for line in diff_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1
        return {
            "additions": additions,
            "deletions": deletions,
            "net_change": additions - deletions
        }

    @staticmethod
    def make_diff_context(filename: str, original_text: str, new_text: str) -> Dict[str, Any]:
        diff_str = DiffPatcher.generate_unified_diff(original_text, new_text, filename)
        stats = DiffPatcher.extract_diff_summary(diff_str)
        
        full_tokens = (len(original_text) + len(new_text)) // 4
        diff_tokens = len(diff_str) // 4
        savings_pct = round(max(0, (full_tokens - diff_tokens) / max(1, full_tokens)) * 100, 1)

        return {
            "filename": filename,
            "diff": diff_str,
            "additions": stats["additions"],
            "deletions": stats["deletions"],
            "full_tokens": full_tokens,
            "diff_tokens": diff_tokens,
            "token_savings_pct": savings_pct
        }

    @classmethod
    def replace_range(cls, original_text: str, start_line: int, end_line: int, replacement_text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Replaces 1-based line range [start_line, end_line] inclusive.
        """
        lines = original_text.splitlines(keepends=True)
        total = len(lines)
        if start_line < 1 or start_line > total + 1 or end_line < start_line - 1:
            return False, original_text, f"Invalid line range: {start_line}-{end_line} (total lines: {total})"

        rep_lines = replacement_text.splitlines(keepends=True) if replacement_text else []
        if replacement_text and not rep_lines[-1].endswith("\n"):
            rep_lines[-1] += "\n"

        s_idx = start_line - 1
        e_idx = min(total, end_line)
        new_lines = lines[:s_idx] + rep_lines + lines[e_idx:]
        return True, "".join(new_lines), None

    @classmethod
    def insert_at_line(cls, original_text: str, line_number: int, content_to_insert: str) -> Tuple[bool, str, Optional[str]]:
        """
        Inserts content at line_number (1-based).
        """
        return cls.replace_range(original_text, line_number, line_number - 1, content_to_insert)

    @classmethod
    def delete_range(cls, original_text: str, start_line: int, end_line: int) -> Tuple[bool, str, Optional[str]]:
        """
        Deletes line range [start_line, end_line] inclusive.
        """
        return cls.replace_range(original_text, start_line, end_line, "")

    @classmethod
    def replace_function(cls, original_text: str, function_name: str, new_function_code: str) -> Tuple[bool, str, Optional[str]]:
        """
        Finds and replaces a function definition by name in Python or JS/TS.
        """
        # Python def pattern
        py_pattern = rf"(def\s+{re.escape(function_name)}\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:[\s\S]*?)(?=\n(?:def\s+|class\s+|\Z))"
        match = re.search(py_pattern, original_text)
        if match:
            new_text = original_text[:match.start()] + new_function_code.strip() + "\n\n" + original_text[match.end():]
            return True, new_text, None

        # JS/TS pattern
        js_pattern = rf"((?:async\s+)?function\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{[\s\S]*?\n\}}|(?:const|let|var)\s+{re.escape(function_name)}\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{{[\s\S]*?\n\}})"
        match_js = re.search(js_pattern, original_text)
        if match_js:
            new_text = original_text[:match_js.start()] + new_function_code.strip() + "\n" + original_text[match_js.end():]
            return True, new_text, None

        return False, original_text, f"Function '{function_name}' definition not found in text."

    @classmethod
    def apply_unified_patch(cls, original_text: str, patch_text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Applies a standard unified diff patch to original text.
        """
        orig_lines = original_text.splitlines()
        patch_lines = patch_text.splitlines()
        
        result_lines = []
        i = 0
        p = 0
        while p < len(patch_lines):
            line = patch_lines[p]
            if line.startswith("@@"):
                # Header e.g. @@ -1,4 +1,5 @@
                match = re.search(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
                if match:
                    orig_start = int(match.group(1)) - 1
                    while i < orig_start and i < len(orig_lines):
                        result_lines.append(orig_lines[i])
                        i += 1
                p += 1
                continue
            
            if line.startswith("+"):
                result_lines.append(line[1:])
            elif line.startswith("-"):
                i += 1
            elif line.startswith(" "):
                if i < len(orig_lines):
                    result_lines.append(orig_lines[i])
                    i += 1
            p += 1

        while i < len(orig_lines):
            result_lines.append(orig_lines[i])
            i += 1

        output = "\n".join(result_lines)
        if original_text.endswith("\n"):
            output += "\n"
        return True, output, None
