import time
from collections import OrderedDict
from typing import Any, Optional, Dict, Tuple

class L1MemoryCache:
    """
    High-performance LRU Cache with TTL expiration and hit/miss tracking.
    """

    def __init__(self, max_items: int = 1000, default_ttl_sec: int = 3600):
        self.max_items = max_items
        self.default_ttl = default_ttl_sec
        self._store: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            self.misses += 1
            return None
            
        value, expiry = self._store[key]
        if time.time() > expiry:
            del self._store[key]
            self.misses += 1
            return None
            
        self._store.move_to_end(key)
        self.hits += 1
        return value

    def set(self, key: str, value: Any, ttl_sec: Optional[int] = None) -> None:
        ttl = ttl_sec if ttl_sec is not None else self.default_ttl
        expiry = time.time() + ttl
        
        if key in self._store:
            del self._store[key]
        elif len(self._store) >= self.max_items:
            # Pop oldest
            self._store.popitem(last=False)
            
        self._store[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()

    def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0
        return {
            "items_count": len(self._store),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": round(hit_rate, 2)
        }
