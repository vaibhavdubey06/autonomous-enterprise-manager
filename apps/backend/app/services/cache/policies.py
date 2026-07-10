from enum import Enum
from pydantic import BaseModel
from typing import Optional


class CachePolicy(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    READ_ONLY = "READ_ONLY"
    WRITE_ONLY = "WRITE_ONLY"
    BYPASS = "BYPASS"


class CacheConfiguration(BaseModel):
    policy: CachePolicy = CachePolicy.ENABLED
    ttl_seconds: Optional[int] = 86400  # Default 24 hours
    similarity_threshold: float = 0.95


class CachePolicyManager:
    """
    Manages cache policies per tenant, workflow pack, or provider.
    """

    def __init__(self):
        self.default_config = CacheConfiguration()
        self.tenant_configs = {}

    def get_config(
        self, tenant_id: str = "default", workflow_id: Optional[str] = None
    ) -> CacheConfiguration:
        # In a real system, this would fetch from a configuration DB.
        return self.tenant_configs.get(tenant_id, self.default_config)

    def allows_read(self, config: CacheConfiguration) -> bool:
        return config.policy in (CachePolicy.ENABLED, CachePolicy.READ_ONLY)

    def allows_write(self, config: CacheConfiguration) -> bool:
        return config.policy in (CachePolicy.ENABLED, CachePolicy.WRITE_ONLY)
