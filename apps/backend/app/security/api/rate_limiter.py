import time
from app.platform.cache.cache_provider import CacheProvider
from app.platform.cache.memory_cache import MemoryCacheProvider


class RateLimiter:
    def __init__(self, calls: int, period: int, cache: CacheProvider = None):
        self.calls = calls
        self.period = period
        self.cache = cache or MemoryCacheProvider()

    def is_rate_limited(self, identifier: str) -> bool:
        now = time.time()
        key = f"rate_limit:{identifier}"

        item = self.cache.get(key)

        if not item:
            self.cache.set(
                key, {"first_call_time": now, "call_count": 1}, ttl=self.period
            )
            return False

        first_call_time = item["first_call_time"]
        call_count = item["call_count"]

        if now - first_call_time > self.period:
            # Reset window
            self.cache.set(
                key, {"first_call_time": now, "call_count": 1}, ttl=self.period
            )
            return False

        if call_count >= self.calls:
            return True

        self.cache.set(
            key,
            {"first_call_time": first_call_time, "call_count": call_count + 1},
            ttl=self.period,
        )
        return False


# Global simple rate limiter: 100 requests per 60 seconds per IP
from app.core.config import settings

redis_url = settings.REDIS_URL
if redis_url:
    from app.platform.cache.redis_cache import RedisCacheProvider

    global_cache = RedisCacheProvider(redis_url)
else:
    global_cache = MemoryCacheProvider()

global_rate_limiter = RateLimiter(calls=100, period=60, cache=global_cache)
