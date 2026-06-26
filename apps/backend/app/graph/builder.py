"""
Graph Builder — Top-level entry point for constructing the LangGraph runtime.

Provides a single `build()` function that wires up services, tool registry,
and graph router.  The API layer calls this once on startup.
"""

import logging

from app.graph.dependencies import ServiceContainer
from app.graph.registry import build_default_registry
from app.graph.router import GraphRouter

logger = logging.getLogger(__name__)


def build(services: ServiceContainer) -> GraphRouter:
    """
    Build the complete LangGraph orchestration layer.

    Args:
        services: Injected ServiceContainer with all business services.

    Returns:
        A GraphRouter ready to execute graphs.
    """
    tool_registry = build_default_registry()
    router = GraphRouter(services=services, tool_registry=tool_registry)
    logger.info("LangGraph orchestration layer built successfully.")
    return router
