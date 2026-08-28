import time
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .normalizer import ApiUrlNormalizer
from ..security.redaction import SecretRedactor

class ModelDiscoveryService:
    """
    Handles discovery, validation, and caching of OpenAI-compatible models.
    Supports OpenAI, OpenRouter, NVIDIA NIM, LocalAI/Ollama, vLLM, and custom endpoints.
    """

    def __init__(self, cache_ttl_seconds: int = 86400):
        self.cache_ttl = cache_ttl_seconds
        # In-memory discovery cache keyed by (provider, base_url)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _cache_key(self, base_url: str) -> str:
        return ApiUrlNormalizer.clean_base_url(base_url).lower()

    async def discover_models(self, base_url: str, api_key: str, force_refresh: bool = False) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
        """
        Discovers models by querying GET <base_url>/models.
        Returns: (success, models_list, error_message)
        """
        key = self._cache_key(base_url)
        now = time.time()

        if not force_refresh and key in self._cache:
            entry = self._cache[key]
            if now - entry["timestamp"] < self.cache_ttl:
                return True, entry["models"], None

        models_url = ApiUrlNormalizer.get_models_url(base_url)
        headers = ApiUrlNormalizer.sanitize_headers(api_key)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, self._http_get_json, models_url, headers)
            raw_models = []
            if isinstance(result, dict):
                # Standard OpenAI format: {"data": [{"id": "...", ...}]}
                raw_models = result.get("data", []) or result.get("models", [])
            elif isinstance(result, list):
                raw_models = result

            parsed_models = []
            for item in raw_models:
                if isinstance(item, dict):
                    model_id = item.get("id") or item.get("name")
                    if model_id:
                        parsed_models.append({
                            "id": model_id,
                            "name": item.get("name", model_id),
                            "context_length": item.get("context_length") or item.get("max_model_len", 8192),
                            "pricing": item.get("pricing", {}),
                            "owned_by": item.get("owned_by", "openai-compatible")
                        })
                elif isinstance(item, str):
                    parsed_models.append({
                        "id": item,
                        "name": item,
                        "context_length": 8192,
                        "pricing": {},
                        "owned_by": "openai-compatible"
                    })

            # Sort alphabetically by id
            parsed_models.sort(key=lambda x: x["id"])

            if not parsed_models:
                # Fallback list if endpoint returned empty
                parsed_models = [
                    {"id": "gpt-4o", "name": "GPT-4o", "context_length": 128000, "pricing": {}},
                    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context_length": 128000, "pricing": {}},
                    {"id": "claude-3-5-sonnet", "name": "Claude 3.5 Sonnet", "context_length": 200000, "pricing": {}},
                ]

            self._cache[key] = {
                "timestamp": now,
                "models": parsed_models,
                "base_url": ApiUrlNormalizer.clean_base_url(base_url)
            }

            return True, parsed_models, None

        except HTTPError as e:
            err_msg = SecretRedactor.redact_text(f"HTTP {e.code}: {e.reason}")
            # If 404 or unsupported /models endpoint, provide sensible curated defaults
            if e.code in (404, 405):
                fallback = [
                    {"id": "default-model", "name": "Default Model", "context_length": 8192, "pricing": {}}
                ]
                return True, fallback, f"Endpoint does not support /models (HTTP {e.code}). Using default fallback."
            return False, [], f"Model discovery failed: {err_msg}"
        except Exception as e:
            return False, [], f"Connection error: {SecretRedactor.redact_text(str(e))}"

    def _http_get_json(self, url: str, headers: dict) -> Any:
        req = Request(url, headers=headers, method="GET")
        with urlopen(req, timeout=12) as response:
            data = response.read().decode("utf-8")
            return json.loads(data)

    async def test_completion(self, base_url: str, api_key: str, model_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Executes a minimal test ping completion to verify the configured model works.
        """
        chat_url = ApiUrlNormalizer.get_chat_completions_url(base_url)
        headers = ApiUrlNormalizer.sanitize_headers(api_key)
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
            "temperature": 0.0
        }

        loop = asyncio.get_event_loop()
        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = Request(chat_url, data=data_bytes, headers=headers, method="POST")
            
            def _post():
                with urlopen(req, timeout=15) as res:
                    return json.loads(res.read().decode("utf-8"))

            response = await loop.run_in_executor(None, _post)
            content = "OK"
            if "choices" in response and len(response["choices"]) > 0:
                msg = response["choices"][0].get("message", {})
                content = msg.get("content", "OK")
            return True, content, None
        except HTTPError as e:
            return False, None, SecretRedactor.redact_text(f"API Test Error HTTP {e.code}: {e.reason}")
        except Exception as e:
            return False, None, SecretRedactor.redact_text(f"API Test Failed: {str(e)}")
