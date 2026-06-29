import time
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


class CircuitBreakerState:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._last_failure_time = 0.0
        self._state = CircuitBreakerState.CLOSED

    def _evaluate_state(self):
        if self._state == CircuitBreakerState.OPEN:
            if time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker transitioned to HALF_OPEN")

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        self._evaluate_state()

        if self._state == CircuitBreakerState.OPEN:
            raise Exception("Circuit breaker is OPEN. Fast failing request.")

        try:
            result = func(*args, **kwargs)
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._state = CircuitBreakerState.CLOSED
                self._failures = 0
                logger.info("Circuit breaker transitioned to CLOSED")
            return result
        except Exception as e:
            self._failures += 1
            self._last_failure_time = time.time()
            if (
                self._failures >= self.failure_threshold
                and self._state != CircuitBreakerState.OPEN
            ):
                self._state = CircuitBreakerState.OPEN
                logger.warning("Circuit breaker transitioned to OPEN")
            raise e

    @property
    def state(self):
        self._evaluate_state()
        return self._state
