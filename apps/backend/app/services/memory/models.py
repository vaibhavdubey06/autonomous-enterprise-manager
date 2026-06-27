from pydantic import BaseModel
from typing import List, Optional
from app.services.memory.types import MemoryType

class ExtractedMemory(BaseModel):
    title: str
    content: str
    memory_type: MemoryType
    source: str = "conversation"
    metadata_: dict = {}
    tags: List[str] = []
    importance: Optional[float] = None
    confidence: Optional[float] = None

class MemoryExtractionResult(BaseModel):
    memories: List[ExtractedMemory]
