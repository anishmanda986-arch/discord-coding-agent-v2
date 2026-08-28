# Coding Agent Configuration
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class SecurityConfig:
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "dev-secret-key-32-chars-minimum-required!"))
    sandbox_enabled: bool = field(default_factory=lambda: os.getenv("SANDBOX_ENABLED", "true").lower() == "true")
    docker_enabled: bool = field(default_factory=lambda: os.getenv("DOCKER_ENABLED", "false").lower() == "true")
    allowed_workspace_root: str = field(default_factory=lambda: os.getenv("WORKSPACE_ROOT", "/tmp/coding_agent_workspaces"))
    max_file_size_bytes: int = 5 * 1024 * 1024  # 5MB
    max_execution_timeout_sec: int = 60
    command_timeout_sec: int = 30
    banned_commands: tuple = (
        "rm -rf /", "mkfs", "dd if=/dev", ":(){ :|:& };:", "shutdown", "reboot",
        "chmod -R 777 /", "chown -R", "wget http", "curl http://169.254.169.254"
    )

@dataclass
class BudgetLimits:
    max_model_calls_per_task: int = 25
    max_tokens_per_task: int = 150_000
    max_tool_calls: int = 40
    max_execution_time_sec: int = 300
    max_context_tokens: int = 16_000
    cost_threshold_warning_usd: float = 0.50

@dataclass
class CacheConfig:
    l1_max_items: int = 1000
    l1_default_ttl_sec: int = 3600
    models_cache_ttl_sec: int = 86400  # 24 hours
    repo_index_ttl_sec: int = 7200
    dedup_window_sec: int = 300

@dataclass
class RateLimitConfig:
    global_rpm: int = 120
    user_rpm: int = 20
    channel_rpm: int = 30
    provider_concurrency_limit: int = 5
    retry_max_attempts: int = 4
    retry_backoff_factors: tuple = (1.0, 2.0, 4.0, 8.0)

@dataclass
class AppConfig:
    discord_token: Optional[str] = field(default_factory=lambda: os.getenv("DISCORD_BOT_TOKEN"))
    discord_app_id: Optional[str] = field(default_factory=lambda: os.getenv("DISCORD_APP_ID"))
    database_path: str = field(default_factory=lambda: os.getenv("DATABASE_PATH", "data/coding_agent.sqlite3"))
    gateway_host: str = field(default_factory=lambda: os.getenv("GATEWAY_HOST", "0.0.0.0"))
    gateway_port: int = field(default_factory=lambda: int(os.getenv("GATEWAY_PORT", "8000")))
    gateway_auth_secret: str = field(default_factory=lambda: os.getenv("GATEWAY_AUTH_SECRET", "gateway-shared-secret-key-prod"))
    default_provider: str = field(default_factory=lambda: os.getenv("DEFAULT_PROVIDER", "openrouter"))
    default_base_url: str = field(default_factory=lambda: os.getenv("DEFAULT_BASE_URL", "https://openrouter.ai/api/v1"))
    default_api_key: Optional[str] = field(default_factory=lambda: os.getenv("DEFAULT_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))
    default_fast_model: str = field(default_factory=lambda: os.getenv("FAST_MODEL", "google/gemini-2.5-flash"))
    default_strong_model: str = field(default_factory=lambda: os.getenv("STRONG_MODEL", "anthropic/claude-3.5-sonnet"))
    github_token: Optional[str] = field(default_factory=lambda: os.getenv("GITHUB_TOKEN"))
    
    security: SecurityConfig = field(default_factory=SecurityConfig)
    budget: BudgetLimits = field(default_factory=BudgetLimits)
    cache: CacheConfig = field(default_factory=CacheConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)

config = AppConfig()
