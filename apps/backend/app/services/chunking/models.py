from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class ChunkMetadata(BaseModel):
    """
    Rich metadata model for an intelligent chunk.
    Maintains compact footprint by delta-storing when possible.
    """
    document_id: str
    document_name: str
    document_version: str = "1.0"
    
    # Optional structural properties
    repository: Optional[str] = None
    branch: Optional[str] = None
    file_path: Optional[str] = None
    language: Optional[str] = None
    page: Optional[int] = None
    
    # Hierarchy
    section: Optional[str] = None
    subsection: Optional[str] = None
    heading: Optional[str] = None
    
    # Pagination / Graph
    chunk_index: int = 0
    total_chunks: int = 0
    parent_chunk: Optional[str] = None
    previous_chunk: Optional[str] = None
    next_chunk: Optional[str] = None
    
    # Intelligence
    token_estimate: int = 0
    semantic_hash: Optional[str] = None
    embedding_version: str = "v1"
    
    # Source
    source: Optional[str] = None
    source_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Chunk(BaseModel):
    """
    Core chunk structure.
    """
    id: str
    text: str
    metadata: ChunkMetadata
    
    def dict_for_qdrant(self) -> Dict[str, Any]:
        """
        Export a flattened dictionary for Qdrant payload.
        We drop empty optional fields to keep the payload compact.
        """
        payload = self.metadata.model_dump(exclude_none=True)
        payload["text"] = self.text
        return payload
