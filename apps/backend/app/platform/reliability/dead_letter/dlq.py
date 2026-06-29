from typing import Dict, Any, List
import json
import time


class DeadLetterQueue:
    def __init__(self, cache_provider):
        self.cache_provider = cache_provider
        self.queue_key = "dlq:events"

    def push(self, event_type: str, payload: Dict[str, Any], error_message: str):
        event = {
            "id": f"dlq-{time.time()}",
            "type": event_type,
            "payload": payload,
            "error": error_message,
            "timestamp": time.time(),
            "retries": 0,
        }

        # Get existing DLQ
        current_dlq = self.cache_provider.get(self.queue_key)
        if current_dlq is None:
            current_dlq = []
        elif isinstance(current_dlq, str):
            current_dlq = json.loads(current_dlq)

        current_dlq.append(event)
        self.cache_provider.set(self.queue_key, json.dumps(current_dlq))

    def pop_all(self) -> List[Dict[str, Any]]:
        current_dlq = self.cache_provider.get(self.queue_key)
        if current_dlq is None:
            return []

        if isinstance(current_dlq, str):
            current_dlq = json.loads(current_dlq)

        self.cache_provider.delete(self.queue_key)
        return current_dlq
