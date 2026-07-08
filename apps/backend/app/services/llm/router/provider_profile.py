from pydantic import BaseModel, Field
from typing import Optional

class ProviderProfile(BaseModel):
    provider_name: str
    model_name: str
    vendor: str
    context_window: int = 8192
    max_output_tokens: int = 4096
    
    # Capabilities
    supports_json: bool = False
    supports_streaming: bool = False
    supports_function_calling: bool = False
    supports_multimodal: bool = False
    supports_reasoning: bool = False
    supports_vision: bool = False
    supports_embeddings: bool = False
    supports_audio: bool = False
    
    # Cost & Classification
    cost_input: float = 0.0  # per 1M tokens
    cost_output: float = 0.0 # per 1M tokens
    latency_class: str = "medium"  # fast, medium, slow
    quality_score: float = 0.5     # 0.0 to 1.0
    reliability_score: float = 0.99
    availability_score: float = 0.99
    
    # Rate limits
    requests_per_minute: int = 60
    tokens_per_minute: int = 100000
    
    # Dynamic health (can be updated externally)
    health_status: str = "healthy"  # healthy, degraded, offline
