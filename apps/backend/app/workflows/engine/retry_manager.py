import asyncio
import logging
from typing import Callable, Any, Dict
from app.workflows.models.task import Task

logger = logging.getLogger(__name__)

class RetryManager:
    @staticmethod
    async def execute_with_retry(task: Task, execute_fn: Callable) -> Any:
        policy = task.retry_policy or {}
        max_retries = policy.get("max_retries", 0)
        strategy = policy.get("strategy", "immediate") # immediate, exponential
        base_delay = policy.get("base_delay_seconds", 1)
        
        attempt = 0
        while True:
            try:
                return await execute_fn(task)
            except Exception as e:
                attempt += 1
                if attempt > max_retries:
                    logger.error(f"Task {task.task_id} failed after {max_retries} retries: {e}")
                    raise
                    
                logger.warning(f"Task {task.task_id} failed on attempt {attempt}. Retrying...")
                
                if strategy == "exponential":
                    delay = base_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
                elif strategy == "immediate":
                    pass # Retry immediately
                else:
                    await asyncio.sleep(base_delay)
