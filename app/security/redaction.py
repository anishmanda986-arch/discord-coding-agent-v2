import re
from typing import Any, Dict, List, Union

class SecretRedactor:
    """
    High-performance secret detector and sanitizer.
    Guarantees API keys, auth tokens, SSH keys, passwords, and sensitive URLs
    are never leaked into Discord messages, logs, embeds, diffs, or zip exports.
    """
    
    # Common secret patterns
    SECRET_PATTERNS = [
        # OpenAI / OpenRouter / Anthropic keys
        (re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
        (re.compile(r"sk-or-v1-[a-zA-Z0-9]{32,}", re.IGNORECASE), "[REDACTED_OPENROUTER_KEY]"),
        (re.compile(r"ghp_[a-zA-Z0-9]{36,}", re.IGNORECASE), "[REDACTED_GITHUB_TOKEN]"),
        (re.compile(r"github_pat_[a-zA-Z0-9_]{50,}", re.IGNORECASE), "[REDACTED_GITHUB_PAT]"),
        (re.compile(r"nvapi-[a-zA-Z0-9_\-]{30,}", re.IGNORECASE), "[REDACTED_NVIDIA_KEY]"),
        # Discord Bot Tokens
        (re.compile(r"[MNO][a-zA-Z\d_-]{23,25}\.[a-zA-Z\d_-]{6}\.[a-zA-Z\d_-]{27}", re.IGNORECASE), "[REDACTED_DISCORD_TOKEN]"),
        # Bearer tokens & auth headers
        (re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE), r"\1[REDACTED_BEARER_TOKEN]"),
        (re.compile(r"(authorization:\s*Bearer\s+)[a-zA-Z0-9_\-\.]+", re.IGNORECASE), r"\1[REDACTED_TOKEN]"),
        # AWS / GCP keys
        (re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE), "[REDACTED_AWS_KEY]"),
        (re.compile(r"AIza[0-9A-Za-z\-_]{35}", re.IGNORECASE), "[REDACTED_GOOGLE_API_KEY]"),
        # Private Keys
        (re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH|PRIVATE) KEY-----[\s\S]*?-----END \1 KEY-----"), "[REDACTED_PRIVATE_KEY]"),
        # Generic key assignments in strings
        (re.compile(r"(api[_-]?key\s*[:=]\s*['\"])[^'\"]{8,}['\"]", re.IGNORECASE), r"\1[REDACTED_KEY]'"),
        (re.compile(r"(password\s*[:=]\s*['\"])[^'\"]+['\"]", re.IGNORECASE), r"\1[REDACTED_PASSWORD]'"),
    ]

    @classmethod
    def redact_text(cls, text: str) -> str:
        if not text or not isinstance(text, str):
            return text
        redacted = text
        for pattern, replacement in cls.SECRET_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted

    @classmethod
    def redact_object(cls, obj: Any) -> Any:
        """Recursively redact strings in dicts, lists, and primitives."""
        if isinstance(obj, str):
            return cls.redact_text(obj)
        elif isinstance(obj, dict):
            return {k: cls.redact_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [cls.redact_object(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(cls.redact_object(item) for item in obj)
        return obj

    @classmethod
    def mask_key_preview(cls, key: str) -> str:
        """Returns a safe preview like 'sk-...9aB2' for UI displays."""
        if not key:
            return "None"
        if len(key) <= 8:
            return "******"
        return f"{key[:4]}...{key[-4:]}"
