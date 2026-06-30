from typing import Any, Optional
import json
from app.platform.cache.cache_provider import CacheProvider


class RedisCacheProvider(CacheProvider):
    def __init__(self, redis_url: str):
        try:
            import redis

            self.client: Optional[Any] = redis.Redis.from_url(
                redis_url, decode_responses=True
            )
        except ImportError:
            # Fallback mock for testing environments where redis package isn't installed
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None
        val = self.client.get(key)
        if val:
            try:
                return json.loads(val)
            except Exception:
                return val
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self.client:
            return
        val = json.dumps(value) if isinstance(value, (dict, list)) else value
        self.client.set(key, val, ex=ttl)

    def delete(self, key: str) -> None:
        if not self.client:
            return
        self.client.delete(key)

    def increment(self, key: str) -> int:
        if not self.client:
            return 1
        return self.client.incr(key)
