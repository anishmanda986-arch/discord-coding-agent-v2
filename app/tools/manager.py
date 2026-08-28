from typing import Dict, Any, List, Optional
from .filesystem import FileSystemTools
from .search import SearchTools
from .terminal import TerminalTools
from .git_tools import GitTools
from .patcher import DiffPatcher

class ToolManager:
    """
    Unified Tool Manager for the Coding Agent.
    Provides schema definitions for OpenAI/OpenRouter function calling
    and executes tool calls with parameter validation.
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.fs = FileSystemTools(workspace_path)
        self.search = SearchTools(workspace_path)
        self.terminal = TerminalTools(workspace_path)
        self.git = GitTools(workspace_path)

    @classmethod
    def get_tool_definitions(cls) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Reads text content from a file in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative file path."},
                            "start_line": {"type": "integer", "description": "Optional 1-indexed start line."},
                            "end_line": {"type": "integer", "description": "Optional 1-indexed end line."}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Atomically writes or creates a file with syntax and size validation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative file path."},
                            "content": {"type": "string", "description": "Full file content."}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Surgically replaces a specific block of text inside a file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative file path."},
                            "target_content": {"type": "string", "description": "Exact text to be replaced."},
                            "replacement_content": {"type": "string", "description": "New replacement text."}
                        },
                        "required": ["path", "target_content", "replacement_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "patch_file",
                    "description": "Performs patch-first modifications (replace_range, insert, delete_range, replace_function).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative file path."},
                            "patch_type": {"type": "string", "enum": ["replace_range", "insert", "delete_range", "replace_function", "unified_diff"]},
                            "start_line": {"type": "integer", "description": "Start line for range edits."},
                            "end_line": {"type": "integer", "description": "End line for range edits."},
                            "line_number": {"type": "integer", "description": "Line number for insert."},
                            "content": {"type": "string", "description": "Content for insert or replacement."},
                            "replacement_text": {"type": "string", "description": "Replacement text for range."},
                            "function_name": {"type": "string", "description": "Name of function to replace."},
                            "new_function_code": {"type": "string", "description": "New function code."},
                            "diff_text": {"type": "string", "description": "Unified diff text."}
                        },
                        "required": ["path", "patch_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_file",
                    "description": "Deletes a file or directory inside the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative path to file or directory."}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tree",
                    "description": "Lists files and directory structure of the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {"type": "string", "description": "Relative directory path (default '.')"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "grep_search",
                    "description": "Searches for regex/text patterns across workspace files.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query or regex."}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_command",
                    "description": "Runs a safe terminal command inside the workspace directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Terminal command to run."}
                        },
                        "required": ["command"]
                    }
                }
            }
        ]

    async def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches tool execution safely with error boundary.
        """
        try:
            if tool_name == "read_file":
                return self.fs.read_file(
                    rel_path=arguments.get("path", ""),
                    start_line=arguments.get("start_line"),
                    end_line=arguments.get("end_line")
                )
            elif tool_name == "write_file":
                return self.fs.write_file(
                    rel_path=arguments.get("path", ""),
                    content=arguments.get("content", "")
                )
            elif tool_name == "edit_file":
                return self.fs.edit_file(
                    rel_path=arguments.get("path", ""),
                    target_content=arguments.get("target_content", ""),
                    replacement_content=arguments.get("replacement_content", "")
                )
            elif tool_name == "patch_file":
                return self.fs.patch_file(
                    rel_path=arguments.get("path", ""),
                    patch_type=arguments.get("patch_type", ""),
                    **arguments
                )
            elif tool_name == "delete_file":
                return self.fs.delete_file(
                    rel_path=arguments.get("path", "")
                )
            elif tool_name == "list_tree":
                return self.fs.list_tree(
                    rel_dir=arguments.get("directory", ".")
                )
            elif tool_name == "grep_search":
                return self.search.grep_search(
                    query=arguments.get("query", "")
                )
            elif tool_name == "execute_command":
                return await self.terminal.execute_command(
                    command=arguments.get("command", "")
                )
            else:
                return {"success": False, "error": f"Unknown tool: '{tool_name}'"}
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}
