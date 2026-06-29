import pytest
import asyncio
from app.platform.reliability.retry.retry_policies import (
    ImmediateRetry,
    ErrorClassification,
)
from app.platform.reliability.circuit_breaker.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
)
from app.platform.reliability.timeout.timeout_policy import TimeoutPolicy
from app.platform.reliability.bulkhead.bulkhead import Bulkhead
from app.platform.reliability.dead_letter.dlq import DeadLetterQueue
from app.platform.reliability.recovery.checkpoint import CheckpointManager
from app.platform.cache.memory_cache import MemoryCacheProvider


def test_immediate_retry():
    retry = ImmediateRetry(max_retries=3)

    calls = 0

    def failing_func():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise Exception("Fail")
        return "Success"

    result = retry.execute(failing_func)
    assert result == "Success"
    assert calls == 3


def test_retry_permanent_error():
    retry = ImmediateRetry(max_retries=3)

    def failing_func():
        raise ValueError("Permanent")

    def classify(e):
        return ErrorClassification.PERMANENT

    with pytest.raises(ValueError):
        retry.execute(failing_func, classify_error=classify)


@pytest.mark.asyncio
async def test_timeout_policy():
    policy = TimeoutPolicy(timeout_seconds=0.1)

    async def slow_func():
        await asyncio.sleep(0.2)

    with pytest.raises(TimeoutError):
        await policy.execute_async(slow_func)


@pytest.mark.asyncio
async def test_bulkhead():
    bulkhead = Bulkhead(max_concurrency=1)

    async def task():
        await asyncio.sleep(0.1)
        return True

    # Start task 1, which will acquire the bulkhead
    t1 = asyncio.create_task(bulkhead.execute_async(task))

    # Let event loop start t1
    await asyncio.sleep(0.01)

    # Task 2 should fail immediately because max_concurrency=1
    with pytest.raises(Exception, match="exhausted"):
        await bulkhead.execute_async(task)

    await t1


def test_circuit_breaker():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    def failing_func():
        raise Exception("Fail")

    with pytest.raises(Exception):
        breaker.execute(failing_func)

    with pytest.raises(Exception):
        breaker.execute(failing_func)

    assert breaker.state == CircuitBreakerState.OPEN


def test_dlq():
    cache = MemoryCacheProvider()
    dlq = DeadLetterQueue(cache)

    dlq.push("TestEvent", {"data": 1}, "Error")
    events = dlq.pop_all()

    assert len(events) == 1
    assert events[0]["type"] == "TestEvent"
    assert events[0]["payload"]["data"] == 1

    assert len(dlq.pop_all()) == 0


def test_checkpoint_manager():
    cache = MemoryCacheProvider()
    manager = CheckpointManager(cache)

    manager.save_checkpoint("wf-1", {"step": 2})
    state = manager.get_checkpoint("wf-1")

    assert state["step"] == 2
    manager.clear_checkpoint("wf-1")
    assert manager.get_checkpoint("wf-1") is None
