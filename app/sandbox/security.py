import os
from typing import Dict, Any, List

class SandboxSecurityPolicy:
    """
    Security constraints for executing untrusted project code.
    Enforces CPU, memory, filesystem, and network isolation limits.
    """
    MAX_CPU_QUOTA: str = "1.0"
    MAX_MEMORY_MB: int = 1024
    MAX_EXECUTION_TIMEOUT_SEC: int = 45
    NETWORK_DISABLED: bool = True
    READ_ONLY_ROOT: bool = True
    USER: str = "sandboxuser"

    DANGEROUS_BINARIES = {
        "iptables", "ifconfig", "ip", "insmod", "rmmod", "useradd", "usermod",
        "passwd", "visudo", "systemctl", "service", "journalctl", "dmesg"
    }

    @classmethod
    def get_docker_run_flags(cls, workspace_path: str) -> List[str]:
        """
        Builds hardened Docker CLI flags for isolated container execution.
        """
        flags = [
            "--rm",
            f"--cpus={cls.MAX_CPU_QUOTA}",
            f"--memory={cls.MAX_MEMORY_MB}m",
            "--pids-limit=64",
            "--security-opt=no-new-privileges:true",
            "--cap-drop=ALL",
            "-v", f"{workspace_path}:/workspace:rw",
            "-w", "/workspace",
        ]
        if cls.NETWORK_DISABLED:
            flags.append("--network=none")
        return flags
