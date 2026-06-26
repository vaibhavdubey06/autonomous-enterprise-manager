"""
Graph Router — Selects and executes the appropriate graph for the workflow type.

Currently only ChatGraph is implemented.
Future graphs are registered here and selected by workflow_type.
"""

import logging
from typing import Dict, Any

from app.graph.state import GraphState
from app.graph.dependencies import ServiceContainer
from app.graph.registry import ToolRegistry
from app.graph.graphs.chat_graph import build_chat_graph

logger = logging.getLogger(__name__)


class GraphRouter:
    """
    Routes execution to the correct compiled graph based on workflow_type.

    New graphs are added by registering them in the constructor.
    No existing code changes required.
    """

    def __init__(self, services: ServiceContainer, tool_registry: ToolRegistry):
        self._services = services
        self._tool_registry = tool_registry

        # Compile graphs once at construction time
        self._graphs: Dict[str, Any] = {
            "chat": build_chat_graph(services, tool_registry),
        }
        # Future:
        # self._graphs["research"] = build_research_graph(services, tool_registry)
        # self._graphs["workflow"] = build_workflow_graph(services, tool_registry)
        # self._graphs["planning"] = build_planning_graph(services, tool_registry)

        logger.info(f"GraphRouter initialised with graphs: {list(self._graphs.keys())}")

    def run(self, initial_state: GraphState) -> GraphState:
        """
        Execute the full graph pipeline.

        The Router Node inside the graph sets `workflow_type`.
        This method currently always runs ChatGraph since it's the
        only compiled graph.  When additional graphs are ready, this
        method will select dynamically.
        """
        # For now, always use "chat". In the future, a pre-routing
        # step could inspect the question to pick the graph.
        graph = self._graphs.get("chat")
        if graph is None:
            raise RuntimeError("ChatGraph is not compiled.")

        logger.info("GraphRouter — invoking ChatGraph")
        result = graph.invoke(initial_state)
        return result
