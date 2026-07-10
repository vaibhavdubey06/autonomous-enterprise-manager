from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import datetime
import uuid


class CacheKey(BaseModel):
    user_question: str
    conversation_context: str = ""
    tenant_id: str = "default"
    org_id: str = "default"
    workspace: str = "default"
    project: str = "default"
    prompt_template_version: str = "latest"
    knowledge_version: str = "latest"
    retrieved_chunk_ids: List[str] = Field(default_factory=list)
    retrieved_chunk_hashes: List[str] = Field(default_factory=list)
    workflow_pack_version: str = "latest"
    model_family: str = "default"
    embedding_model_version: str = "default"


class CacheMetadata(BaseModel):
    ttl_seconds: Optional[int] = None
    prompt_template_version: str = "latest"
    workflow_version: str = "latest"
    knowledge_version: str = "latest"
    retrieved_chunk_ids: List[str] = Field(default_factory=list)
    retrieved_chunk_hashes: List[str] = Field(default_factory=list)
    model: str = "default"
    provider: str = "default"
    token_usage: int = 0
    estimated_cost: float = 0.0
    tenant_id: str = "default"


class CacheEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_question: str
    prompt_embedding: List[float] = Field(default_factory=list)
    response_content: str
    metadata: CacheMetadata
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    expires_at: Optional[datetime.datetime] = None
