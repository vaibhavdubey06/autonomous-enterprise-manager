"""Graph Router for workflow-specific LangGraph execution."""

import logging
from typing import Dict, Any

from app.graph.state import GraphState
from app.graph.dependencies import ServiceContainer
from app.graph.registry import ToolRegistry
from app.graph.graphs.analytics_graph import build_analytics_graph
from app.graph.graphs.chat_graph import build_chat_graph
from app.graph.graphs.executive_decision_graph import (
    build_executive_decision_graph,
)
from app.graph.graphs.incident_response_graph import (
    build_incident_response_graph,
)
from app.graph.graphs.planning_graph import build_planning_graph
from app.graph.graphs.research_graph import build_research_graph
from app.graph.graphs.workflow_graph import build_workflow_graph

logger = logging.getLogger(__name__)


class GraphRouter:
    """
    Routes execution to the correct compiled graph based on workflow_type.

    New graphs are added by registering them in the constructor.
    No existing code changes required.
    """

    def __init__(
        self,
        services: ServiceContainer,
        tool_registry: ToolRegistry,
    ):
        self._services = services
        self._tool_registry = tool_registry

        # Compile graphs once at construction time
        self._graphs: Dict[str, Any] = {
            "chat": build_chat_graph(services, tool_registry),
            "research": build_research_graph(services, tool_registry),
            "planning": build_planning_graph(services, tool_registry),
            "workflow": build_workflow_graph(services, tool_registry),
            "analytics": build_analytics_graph(services, tool_registry),
            "executive_decision": build_executive_decision_graph(
                services, tool_registry
            ),
            "incident_response": build_incident_response_graph(
                services, tool_registry
            ),
        }

        logger.info(
            "GraphRouter initialised with graphs: %s",
            list(self._graphs.keys()),
        )

    def _resolve_graph_key(self, initial_state: GraphState) -> str:
        workflow_type = initial_state.get("workflow_type", "chat")
        if workflow_type in self._graphs:
            return workflow_type
        logger.warning(
            "GraphRouter received unknown workflow_type='%s', "
            "falling back to chat",
            workflow_type,
        )
        return "chat"

    def run(self, initial_state: GraphState) -> GraphState:
        """
        Execute the full graph pipeline.

        The Router Node inside the graph sets `workflow_type`.
        This method selects the matching compiled graph and falls back
        to ChatGraph for unknown workflow types.
        """
        graph_key = self._resolve_graph_key(initial_state)
        graph = self._graphs.get(graph_key)
        if graph is None:
            raise RuntimeError(f"Graph '{graph_key}' is not compiled.")

        logger.info("GraphRouter — invoking %s graph", graph_key)
        result = graph.invoke(initial_state)
        return result
