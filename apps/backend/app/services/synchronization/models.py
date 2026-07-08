from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class SyncChunk(BaseModel):
    chunk_id: str
    chunk_hash: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SyncDocument(BaseModel):
    document_id: str
    source_url: Optional[str] = None
    version: str
    sha: str
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunks: List[SyncChunk] = Field(default_factory=list)

class ResourceRegistryEntry(BaseModel):
    resource_id: str
    connector_id: str
    resource_type: str  # "repository", "channel", "file", "folder"
    name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CheckpointModel(BaseModel):
    connector_id: str
    resource_id: str
    last_synced_at: datetime
    state: Optional[Dict[str, Any]] = None
