import os
import re
import shlex
from pathlib import Path
from typing import Tuple, Optional, List

class SecurityValidator:
    """
    Validates input paths, commands, and arguments to prevent path traversal,
    arbitrary command execution escapes, and malicious inputs.
    """
    
    FORBIDDEN_COMMANDS = {
        "rm -rf /", "rm -rf /*", "mkfs", "dd", "shutdown", "reboot",
        "poweroff", "init 0", "forkbomb", ":(){ :|:& };:", "nc -e",
        "bash -i", "/dev/tcp", "curl -s http://169.254.169.254", "wget http://169.254.169.254"
    }

    DANGEROUS_SUBSTRINGS = [
        "../", "..\\", "/etc/passwd", "/etc/shadow", "/var/run/docker.sock",
        "~/.ssh", "~/.aws", ".env"
    ]

    @staticmethod
    def validate_workspace_path(base_workspace: str, target_relative_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates that target_relative_path stays strictly inside base_workspace.
        Resolves symlinks and canonicalizes the path.
        Returns: (is_valid, resolved_path_or_none, error_message_or_none)
        """
        try:
            base_path = Path(base_workspace).resolve()
            
            # Reject absolute paths or paths with null bytes
            if "\0" in target_relative_path:
                return False, None, "Invalid path: contains null bytes."
                
            clean_rel = os.path.normpath(target_relative_path).lstrip("/\\")
            if clean_rel.startswith("..") or "/../" in clean_rel or "\\..\\" in clean_rel:
                return False, None, "Path traversal attempt detected."
                
            target_path = (base_path / clean_rel).resolve()
            
            # Check if resolved path is inside base_path
            try:
                target_path.relative_to(base_path)
            except ValueError:
                return False, None, f"Access denied: path '{target_relative_path}' resolves outside workspace boundary."
                
            return True, str(target_path), None
        except Exception as e:
            return False, None, f"Path validation error: {str(e)}"

    @staticmethod
    def is_safe_command(command: str) -> Tuple[bool, Optional[str]]:
        """
        Validates command against banned patterns and root destruction heuristics.
        """
        if not command or not command.strip():
            return False, "Empty command."
            
        cmd_lower = command.strip().lower()
        
        for banned in SecurityValidator.FORBIDDEN_COMMANDS:
            if banned in cmd_lower:
                return False, f"Command rejected: contains forbidden instruction '{banned}'"
                
        # Reject direct destructive flags against root or system dirs
        if re.search(r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f*|-f[a-zA-Z]*r[a-zA-Z]*)\s+(/|/\*|\.\./|~)", cmd_lower):
            return False, "Destructive deletion command targeted at root or parent directory rejected."
            
        if re.search(r">\s*(/etc|/dev/sda|/dev/nvme|/boot)", cmd_lower):
            return False, "Direct raw disk / system redirection rejected."
            
        return True, None

    @staticmethod
    def sanitize_project_name(name: str) -> str:
        """
        Cleans project name to alphanumeric, underscores, hyphens only.
        """
        clean = re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip())
        return clean[:64] or "project"
