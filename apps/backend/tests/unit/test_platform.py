import pytest
from app.platform.configuration.runtime_profiles import EnvironmentProfile
from app.platform.configuration.configuration_service import ConfigurationService
from app.platform.cache.memory_cache import MemoryCacheProvider
from app.platform.cache.redis_cache import RedisCacheProvider
from app.platform.discovery.service_registry import ServiceRegistry
from app.platform.resilience.policies import RetryPolicy, CircuitBreaker
import time
import unittest.mock as mock


def test_configuration_service():
    config_dev = ConfigurationService(EnvironmentProfile.DEVELOPMENT)
    assert config_dev.get("LOG_LEVEL") == "DEBUG"

    config_prod = ConfigurationService(EnvironmentProfile.PRODUCTION)
    assert config_prod.get("LOG_LEVEL") == "WARNING"

    config_prod.set_override("NEW_KEY", "value")
    assert config_prod.get("NEW_KEY") == "value"


def test_memory_cache_provider():
    cache = MemoryCacheProvider()
    cache.set("key1", "value1", ttl=1)
    assert cache.get("key1") == "value1"

    time.sleep(1.1)
    assert cache.get("key1") is None

    cache.increment("counter")
    assert cache.get("counter") == 1
    cache.increment("counter")
    assert cache.get("counter") == 2

    cache.delete("counter")
    assert cache.get("counter") is None


def test_redis_cache_provider():
    # Mock redis client behavior
    mock_redis = mock.MagicMock()
    mock_client = mock.MagicMock()
    mock_redis.Redis.from_url.return_value = mock_client

    with mock.patch.dict("sys.modules", {"redis": mock_redis}):
        cache = RedisCacheProvider("redis://localhost:6379")

        # set
        cache.set("key1", "value1", ttl=10)
        mock_client.set.assert_called_with("key1", "value1", ex=10)

        # get
        mock_client.get.return_value = '"value1"'
        assert cache.get("key1") == "value1"

        # delete
        cache.delete("key1")
        mock_client.delete.assert_called_with("key1")

        # increment
        mock_client.incr.return_value = 2
        assert cache.increment("counter") == 2


def test_service_registry():
    registry = ServiceRegistry(EnvironmentProfile.DEVELOPMENT)
    assert registry.get_service_url("backend") == "http://backend:8000"

    prod_registry = ServiceRegistry(EnvironmentProfile.PRODUCTION)
    assert (
        prod_registry.get_service_url("postgres")
        == "postgres.data.svc.cluster.local:5432"
    )


def test_retry_policy():
    policy = RetryPolicy(max_retries=3, backoff=0.01)

    calls = 0

    def failing_func():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise Exception("Fail")
        return "Success"

    result = policy.execute(failing_func)
    assert result == "Success"
    assert calls == 3


def test_circuit_breaker():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    def failing_func():
        raise Exception("Fail")

    def success_func():
        return "Success"

    with pytest.raises(Exception):
        breaker.execute(failing_func)

    with pytest.raises(Exception):
        breaker.execute(failing_func)

    # Circuit should now be OPEN
    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        breaker.execute(success_func)

    # Wait for recovery timeout
    time.sleep(0.15)

    # Circuit should be HALF_OPEN and succeed, then transition to CLOSED
    assert breaker.execute(success_func) == "Success"
