import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List

@dataclass
class ChannelConfig:
    channel_id: str
    guild_id: Optional[str] = None
    is_disabled: bool = False
    active_project_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

@dataclass
class ApiConfiguration:
    id: str  # e.g., "channel:<channel_id>" or "user:<user_id>" or "global"
    provider: str
    base_url: str
    api_key_encrypted: str
    selected_model: str
    fast_model: Optional[str] = None
    strong_model: Optional[str] = None
    cached_models_json: Optional[str] = None
    last_validated_at: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

@dataclass
class ProjectEntity:
    project_id: str
    name: str
    workspace_path: str
    persistence_mode: str = "TEMPORARY"  # "TEMPORARY" or "PERSISTENT"
    github_repo: Optional[str] = None
    github_branch: Optional[str] = "main"
    language: Optional[str] = None
    framework: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_accessed_at: float = field(default_factory=time.time)

@dataclass
class TaskStep:
    step_id: str
    task_id: str
    agent: str
    action: str
    status: str  # "RUNNING", "SUCCESS", "FAILED"
    details: str
    tokens_used: int = 0
    duration_ms: int = 0
    created_at: float = field(default_factory=time.time)

@dataclass
class TaskEntity:
    task_id: str
    project_id: str
    user_id: str
    channel_id: str
    prompt: str
    complexity: str = "MEDIUM"  # TRIVIAL, SMALL, MEDIUM, LARGE, COMPLEX
    status: str = "PENDING"     # PENDING, ANALYZING, IMPLEMENTING, TESTING, PACKAGING, COMPLETED, FAILED
    error_message: Optional[str] = None
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_model_calls: int = 0
    total_tool_calls: int = 0
    estimated_cost_usd: float = 0.0
    files_changed: List[str] = field(default_factory=list)
    deliverable_path: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
