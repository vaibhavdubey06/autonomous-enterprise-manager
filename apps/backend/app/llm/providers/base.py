"""Enterprise LLM Orchestration Platform - Provider and Model interfaces."""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ModelCapability(Enum):
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    SUMMARIZATION = "summarization"
    EMBEDDING = "embedding"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"


class InferenceRequest:
    """Standardized inference request across all providers."""

    def __init__(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        capability: ModelCapability = ModelCapability.TEXT_GENERATION,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.prompt = prompt
        self.model_id = model_id
        self.capability = capability
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.metadata = metadata or {}


class InferenceResponse:
    """Standardized inference response from any provider."""

    def __init__(
        self,
        content: str,
        provider: str,
        model: str,
        tokens_used: int = 0,
        latency_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.content = content
        self.provider = provider
        self.model = model
        self.tokens_used = tokens_used
        self.latency_ms = latency_ms
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
        }


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def get_name(self) -> str: ...

    @abstractmethod
    def get_supported_models(self) -> List[str]: ...

    @abstractmethod
    def get_capabilities(self) -> List[ModelCapability]: ...

    @abstractmethod
    def invoke(self, request: InferenceRequest) -> InferenceResponse: ...

    @abstractmethod
    def is_available(self) -> bool: ...
