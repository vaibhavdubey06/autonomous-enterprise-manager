import asyncio
from typing import Callable, Any


class Bulkhead:
    def __init__(self, max_concurrency: int):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.max_concurrency = max_concurrency

    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        if self.semaphore.locked():
            raise Exception(
                "Bulkhead capacity exhausted. Rejecting request to prevent cascading failure."
            )

        async with self.semaphore:
            return await func(*args, **kwargs)
