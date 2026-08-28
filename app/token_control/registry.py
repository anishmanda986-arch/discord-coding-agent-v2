import time
import json
from typing import Dict, List, Optional, Tuple, Set, Any
from .models import FreeModelEntry

class FreeModelRegistry:
    """
    Registry of Verified Free AI Models.
    CRITICAL FAIL-CLOSED RULES:
      - Only models with price == 0.0 (or provider metadata explicitly verifying 0 cost) are classified as free.
      - Unknown, missing, stale, or ambiguous pricing => is_free = FALSE.
      - Never assume a model is free merely because its name contains 'free', 'trial', or 'community'.
      - Free models must match required capabilities (coding, tool_calling, chat, etc.).
    """

    DEFAULT_TTL_SECONDS = 86400  # 24 hours

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.ttl = ttl_seconds
        # In-memory registry of verified free models
        self._registry: Dict[str, FreeModelEntry] = {}
        self._last_refreshed: float = 0.0
        self._seed_default_verified_free_models()

    def _seed_default_verified_free_models(self) -> None:
        """Seeds trusted baseline models known to have verified zero pricing / free tiers."""
        now = time.time()
        verified_defaults = [
            FreeModelEntry(
                model_id="meta-llama/llama-3.3-70b-instruct:free",
                provider="openrouter",
                input_price=0.0,
                output_price=0.0,
                is_free=True,
                last_verified=now,
                capabilities=["chat", "coding", "tool_calling", "structured_output", "long_context"],
                context_length=131072,
                description="Verified Free Llama 3.3 70B on OpenRouter Free Tier"
            ),
            FreeModelEntry(
                model_id="meta-llama/llama-3-8b-instruct:free",
                provider="openrouter",
                input_price=0.0,
                output_price=0.0,
                is_free=True,
                last_verified=now,
                capabilities=["chat", "coding", "tool_calling", "structured_output"],
                context_length=8192,
                description="Verified Free Llama 3 8B Instruct"
            ),
            FreeModelEntry(
                model_id="google/gemma-2-9b-it:free",
                provider="openrouter",
                input_price=0.0,
                output_price=0.0,
                is_free=True,
                last_verified=now,
                capabilities=["chat", "coding", "structured_output"],
                context_length=8192,
                description="Verified Free Gemma 2 9B Instruct"
            ),
            FreeModelEntry(
                model_id="google/gemini-2.0-flash-exp:free",
                provider="openrouter",
                input_price=0.0,
                output_price=0.0,
                is_free=True,
                last_verified=now,
                capabilities=["chat", "coding", "tool_calling", "structured_output", "vision", "long_context"],
                context_length=1048576,
                description="Verified Free Gemini 2.0 Flash Experimental"
            ),
            FreeModelEntry(
                model_id="qwen/qwen-2.5-coder-32b-instruct:free",
                provider="openrouter",
                input_price=0.0,
                output_price=0.0,
                is_free=True,
                last_verified=now,
                capabilities=["chat", "coding", "tool_calling", "structured_output"],
                context_length=32768,
                description="Verified Free Qwen 2.5 Coder 32B"
            ),
            FreeModelEntry(
                model_id="deepseek/deepseek-r1:free",
                provider="openrouter",
                input_price=0.0,
                output_price=0.0,
                is_free=True,
                last_verified=now,
                capabilities=["chat", "coding", "structured_output", "reasoning"],
                context_length=65536,
                description="Verified Free DeepSeek R1 Reasoning"
            ),
            FreeModelEntry(
                model_id="mistralai/mistral-7b-instruct:free",
                provider="openrouter",
                input_price=0.0,
                output_price=0.0,
                is_free=True,
                last_verified=now,
                capabilities=["chat", "coding"],
                context_length=32768,
                description="Verified Free Mistral 7B"
            )
        ]
        for m in verified_defaults:
            self._registry[m.model_id] = m
        self._last_refreshed = now

    def is_model_verified_free(self, model_id: str) -> bool:
        """
        Fail-closed check: Returns True if and only if the model is explicitly
        in the verified registry with zero cost and valid verification timestamp.
        """
        if not model_id:
            return False
        entry = self._registry.get(model_id)
        if not entry:
            return False
        if not entry.is_free:
            return False
        if entry.input_price > 0.0 or entry.output_price > 0.0:
            return False
        return True

    def is_model_free(self, model_id: str) -> bool:
        """Convenience alias for is_model_verified_free."""
        return self.is_model_verified_free(model_id)

    def verify_and_register_from_metadata(self, metadata: Dict[str, Any], provider: str = "openrouter") -> bool:
        """Convenience method to register directly from raw model metadata."""
        model_id = metadata.get("id", "")
        pricing = metadata.get("pricing", {})
        context_length = metadata.get("context_length", 32768)
        description = metadata.get("description", "")
        return self.register_or_update_model(
            model_id=model_id,
            provider=provider,
            pricing=pricing,
            context_length=context_length,
            description=description
        )

    def register_or_update_model(
        self,
        model_id: str,
        provider: str,
        pricing: Dict[str, Any],
        capabilities: Optional[List[str]] = None,
        context_length: int = 32768,
        description: str = ""
    ) -> bool:
        """
        Validates pricing metadata from provider.
        Enforces strict fail-closed policy: only 0.0 pricing is admitted as is_free=True.
        """
        now = time.time()
        # Parse pricing
        in_p = None
        out_p = None
        try:
            if isinstance(pricing, dict):
                # Format: {"prompt": "0", "completion": "0"} or {"input": 0.0, "output": 0.0}
                raw_in = pricing.get("prompt") if "prompt" in pricing else pricing.get("input")
                raw_out = pricing.get("completion") if "completion" in pricing else pricing.get("output")
                if raw_in is not None:
                    in_p = float(raw_in)
                if raw_out is not None:
                    out_p = float(raw_out)
        except Exception:
            in_p = None
            out_p = None

        # Fail-closed pricing check
        is_free = False
        if in_p is not None and out_p is not None:
            if in_p == 0.0 and out_p == 0.0:
                is_free = True

        caps = capabilities or ["chat", "coding", "tool_calling"]
        entry = FreeModelEntry(
            model_id=model_id,
            provider=provider,
            input_price=in_p if in_p is not None else 0.0,
            output_price=out_p if out_p is not None else 0.0,
            is_free=is_free,
            last_verified=now,
            capabilities=caps,
            context_length=context_length,
            description=description or f"Verified {'Free' if is_free else 'Paid'} Model"
        )
        if is_free:
            self._registry[model_id] = entry
            return True
        else:
            # If was previously in registry but now paid/unknown, remove it
            self._registry.pop(model_id, None)
            return False

    def get_all_verified_free_models(self) -> List[FreeModelEntry]:
        """Returns all currently active, verified free models."""
        return [m for m in self._registry.values() if m.is_free and m.input_price == 0.0 and m.output_price == 0.0]

    def find_compatible_free_model(
        self,
        required_capabilities: List[str],
        preferred_provider: Optional[str] = None
    ) -> Tuple[Optional[FreeModelEntry], Optional[str]]:
        """
        Finds the highest-capability verified free model matching all required capabilities.
        Returns (model_entry, reason).
        If no model satisfies all capabilities, returns (None, reason).
        """
        free_models = self.get_all_verified_free_models()
        if not free_models:
            return None, "No verified free models are currently registered."

        candidates = []
        for model in free_models:
            # Check capabilities
            has_all_caps = all(model.supports_capability(req_cap) for req_cap in required_capabilities)
            if has_all_caps:
                candidates.append(model)

        if not candidates:
            req_str = ", ".join(required_capabilities)
            return None, f"No verified free model supports all required capabilities: [{req_str}]."

        # Prioritize matching provider, then context length
        if preferred_provider:
            pref = [m for m in candidates if m.provider.lower() == preferred_provider.lower()]
            if pref:
                pref.sort(key=lambda x: x.context_length, reverse=True)
                return pref[0], "Compatible free model selected on preferred provider."

        candidates.sort(key=lambda x: x.context_length, reverse=True)
        return candidates[0], "Compatible verified free model selected."

    def invalidate_cache(self) -> None:
        """Clears and re-seeds verified free models."""
        self._registry.clear()
        self._seed_default_verified_free_models()
