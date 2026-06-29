import asyncio
from typing import Callable, Any


class TimeoutPolicy:
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds

    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        try:
            return await asyncio.wait_for(
                func(*args, **kwargs), timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Execution exceeded timeout of {self.timeout_seconds} seconds"
            )
