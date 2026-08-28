import hashlib
import json
import time
from typing import Dict, Any, Optional

class RequestDeduplicator:
    """
    Prevents duplicate expensive model requests.
    Hashes (provider, model, messages, tools) and tracks in-flight and recent results.
    """

    def __init__(self, ttl_sec: int = 300):
        self.ttl_sec = ttl_sec
        # hash -> {"result": Any, "timestamp": float}
        self._cache: Dict[str, Dict[str, Any]] = {}
        # In-flight task locks
        self._in_flight: Dict[str, float] = {}

    def compute_hash(self, provider: str, model: str, messages: list, tools: list = None) -> str:
        payload = {
            "p": provider,
            "m": model,
            "msg": messages,
            "t": tools or []
        }
        raw_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def get_cached_result(self, req_hash: str) -> Optional[Any]:
        now = time.time()
        if req_hash in self._cache:
            entry = self._cache[req_hash]
            if now - entry["timestamp"] < self.ttl_sec:
                return entry["result"]
            else:
                del self._cache[req_hash]
        return None

    def store_result(self, req_hash: str, result: Any) -> None:
        self._cache[req_hash] = {
            "result": result,
            "timestamp": time.time()
        }
        if req_hash in self._in_flight:
            del self._in_flight[req_hash]

    def is_in_flight(self, req_hash: str) -> bool:
        if req_hash in self._in_flight:
            # If in flight for more than 60s, assume stale
            if time.time() - self._in_flight[req_hash] > 60:
                del self._in_flight[req_hash]
                return False
            return True
        return False

    def mark_in_flight(self, req_hash: str) -> None:
        self._in_flight[req_hash] = time.time()
