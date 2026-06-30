import time
import random
import logging
from typing import Callable, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorClassification(Enum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"


class RetryStrategy:
    def execute(
        self,
        func: Callable,
        *args,
        classify_error: Optional[Callable[[Exception], ErrorClassification]] = None,
        **kwargs,
    ) -> Any:
        raise NotImplementedError


class ImmediateRetry(RetryStrategy):
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def execute(
        self,
        func: Callable,
        *args,
        classify_error: Optional[Callable[[Exception], ErrorClassification]] = None,
        **kwargs,
    ) -> Any:
        attempts = 0
        while attempts < self.max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if (
                    classify_error
                    and classify_error(e) == ErrorClassification.PERMANENT
                ):
                    logger.error(f"Permanent error encountered: {e}. Aborting retries.")
                    raise e

                attempts += 1
                if attempts >= self.max_retries:
                    raise e


class ExponentialBackoffRetry(RetryStrategy):
    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        jitter: bool = False,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

    def execute(
        self,
        func: Callable,
        *args,
        classify_error: Optional[Callable[[Exception], ErrorClassification]] = None,
        **kwargs,
    ) -> Any:
        attempts = 0
        while attempts < self.max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if (
                    classify_error
                    and classify_error(e) == ErrorClassification.PERMANENT
                ):
                    raise e

                attempts += 1
                if attempts >= self.max_retries:
                    raise e

                delay = min(self.max_delay, self.base_delay * (2 ** (attempts - 1)))
                if self.jitter:
                    delay = random.uniform(0, delay)

                time.sleep(delay)
