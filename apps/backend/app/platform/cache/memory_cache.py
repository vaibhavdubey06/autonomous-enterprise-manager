from typing import Any, Optional, Dict
import time
from app.platform.cache.cache_provider import CacheProvider


class MemoryCacheProvider(CacheProvider):
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._cache.get(key)
        if not item:
            return None
        if item.get("expires_at") and time.time() > item["expires_at"]:
            self.delete(key)
            return None
        return item["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expires_at = time.time() + ttl if ttl else None
        self._cache[key] = {"value": value, "expires_at": expires_at}

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def increment(self, key: str) -> int:
        val = self.get(key)
        if val is None:
            val = 0
        val += 1
        # To maintain TTL, we could fetch the item block directly, but for this mock we just overwrite
        # Let's preserve expiration
        item = self._cache.get(key)
        expires_at = item["expires_at"] if item else None
        self._cache[key] = {"value": val, "expires_at": expires_at}
        return val
