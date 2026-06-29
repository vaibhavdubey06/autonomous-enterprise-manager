from typing import Callable, Any


class FallbackStrategy:
    def __init__(self, fallback_func: Callable):
        self.fallback_func = fallback_func

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return self.fallback_func(e, *args, **kwargs)

    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            return await self.fallback_func(e, *args, **kwargs)
