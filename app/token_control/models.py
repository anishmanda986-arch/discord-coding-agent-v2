import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Set

class ModelSwitchState(str, Enum):
    NORMAL = "NORMAL"
    FREE_FALLBACK = "FREE_FALLBACK"
    LIMIT_REACHED = "LIMIT_REACHED"
    NO_FREE_MODEL = "NO_FREE_MODEL"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    RATE_LIMITED = "RATE_LIMITED"

@dataclass
class TokenLimitsConfig:
    daily_limit: int = 100_000
    monthly_limit: int = 2_000_000
    task_limit: int = 50_000
    max_output_tokens: int = 4_096

@dataclass
class FreeModelEntry:
    model_id: str
    provider: str
    input_price: float = 0.0
    output_price: float = 0.0
    is_free: bool = True
    last_verified: float = field(default_factory=time.time)
    capabilities: List[str] = field(default_factory=lambda: ["chat", "coding", "tool_calling", "structured_output"])
    context_length: int = 32_768
    description: str = "Verified Zero-Cost Free Model"

    def supports_capability(self, capability: str) -> bool:
        return capability.lower() in [c.lower() for c in self.capabilities]

@dataclass
class UserTokenRecord:
    user_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    task_tokens: int = 0
    daily_tokens: int = 0
    monthly_tokens: int = 0
    model_calls_paid: int = 0
    model_calls_free: int = 0
    estimated_cost_usd: float = 0.0
    rate_limit_events: int = 0
    auto_switches: int = 0
    current_mode: str = "NORMAL"
    active_model: str = "anthropic/claude-3.5-sonnet"
    provider: str = "openrouter"
    free_fallback_enabled: bool = True

@dataclass
class TokenReservation:
    reservation_id: str
    user_id: str
    task_id: str
    reserved_tokens: int
    created_at: float = field(default_factory=time.time)

@dataclass
class RouteDecision:
    selected_model: str
    status: str
    action: str = "PROCEED"
    is_free_model: bool = False
    notification: Optional[str] = None

    def __iter__(self):
        return iter((self.selected_model, self.status, self.notification, self.is_free_model))

    def __getitem__(self, item):
        return (self.selected_model, self.status, self.notification, self.is_free_model)[item]


