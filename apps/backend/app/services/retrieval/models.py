from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RetrievedChunk(BaseModel):
    id: str
    text: str
    score: float
    source: str = "pdf"
    repository: str = ""
    path: str = ""
    url: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    citation: Optional[str] = None


class QueryContext(BaseModel):
    raw_query: str
    rewritten_queries: List[str] = Field(default_factory=list)
    intent: str = "unknown"
    inferred_capabilities: List[str] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)
    dynamic_top_k: int = 5
    is_complex: bool = False


class RetrievalResult(BaseModel):
    chunks: List[RetrievedChunk] = Field(default_factory=list)
    context: QueryContext
    strategy_used: str
    latency_ms: Dict[str, float] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
