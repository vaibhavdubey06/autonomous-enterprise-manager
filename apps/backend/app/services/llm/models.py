from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration for an LLM generation request."""

    temperature: float = 0.0
    top_p: float = 0.95
    max_output_tokens: int = 2048
    model_name: Optional[str] = None
    timeout: int = 60
    retry_count: int = 3


class LLMRequest(BaseModel):
    """Provider-agnostic request model."""

    prompt: str
    context: Optional[List[str]] = None
    system_instruction: Optional[str] = None
    schema: Optional[type[BaseModel]] = None
    config: LLMConfig = Field(default_factory=LLMConfig)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Provider-agnostic response model."""

    content: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    model_used: str
    provider: str
    latency_ms: float
    cached: bool = False


class PipelineContext(BaseModel):
    """Context object passed through the middleware pipeline."""

    request: LLMRequest
    response: Optional[LLMResponse] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
