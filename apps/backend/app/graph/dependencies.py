"""
ServiceContainer — Dependency injection container for LangGraph nodes.

Nodes never instantiate services. They receive this container
which bundles every service the graph might need.
"""

from dataclasses import dataclass

from app.services.llm.llm_service import LLMService
from app.services.reranking.cross_encoder_service import CrossEncoderService
from app.services.memory_service import MemoryService


@dataclass(frozen=True)
class ServiceContainer:
    """
    Immutable bundle of all services available to graph nodes.

    Passed into node factory functions so nodes never import
    or instantiate services themselves.
    """
    memory_service: MemoryService
    llm_service: LLMService
    cross_encoder_service: CrossEncoderService
