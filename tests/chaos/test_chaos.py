import random
from app.platform.reliability.fallback.fallback_strategy import FallbackStrategy


def test_chaos_redis_failure():
    # Simulate a chaotic Redis failure
    def faulty_redis_get(key):
        if random.random() < 1.0:  # 100% failure for test
            raise ConnectionError("Redis is down!")
        return "data"

    def memory_fallback(e, key):
        assert isinstance(e, ConnectionError)
        return "fallback_data"

    strategy = FallbackStrategy(memory_fallback)

    result = strategy.execute(faulty_redis_get, "my_key")
    assert result == "fallback_data"
