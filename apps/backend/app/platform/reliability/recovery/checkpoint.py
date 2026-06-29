from typing import Dict, Any, Optional
import time


class CheckpointManager:
    def __init__(self, cache_provider):
        self.cache_provider = cache_provider

    def save_checkpoint(self, workflow_id: str, state: Dict[str, Any]):
        key = f"checkpoint:{workflow_id}"
        payload = {"state": state, "timestamp": time.time()}
        self.cache_provider.set(key, payload)

    def get_checkpoint(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        key = f"checkpoint:{workflow_id}"
        data = self.cache_provider.get(key)
        if data:
            return data.get("state")
        return None

    def clear_checkpoint(self, workflow_id: str):
        key = f"checkpoint:{workflow_id}"
        self.cache_provider.delete(key)
