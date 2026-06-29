from typing import Callable, Any
import time


class RetryPolicy:
    def __init__(self, max_retries: int = 3, backoff: float = 1.0):
        self.max_retries = max_retries
        self.backoff = backoff

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        attempts = 0
        while attempts < self.max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                attempts += 1
                if attempts >= self.max_retries:
                    raise e
                time.sleep(self.backoff * attempts)
        raise Exception("Max retries exceeded")


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._last_failure_time = 0.0
        self._state = (
            "CLOSED"  # CLOSED (normal), OPEN (failing, blocked), HALF_OPEN (testing)
        )

    def _evaluate_state(self):
        if self._state == "OPEN":
            if time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = "HALF_OPEN"

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        self._evaluate_state()

        if self._state == "OPEN":
            raise Exception("Circuit breaker is OPEN. Fast failing request.")

        try:
            result = func(*args, **kwargs)
            if self._state == "HALF_OPEN":
                self._state = "CLOSED"
                self._failures = 0
            return result
        except Exception as e:
            self._failures += 1
            self._last_failure_time = time.time()
            if self._failures >= self.failure_threshold:
                self._state = "OPEN"
            raise e
