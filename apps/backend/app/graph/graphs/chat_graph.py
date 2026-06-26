"""
Chat Graph — The primary conversational RAG graph.

START → Router → Planner → Memory → Retrieval → [Tool?] → Context → Response → Validation → END
"""

import logging
from langgraph.graph import StateGraph, START, END

from app.graph.state import GraphState
from app.graph.dependencies import ServiceContainer
from app.graph.registry import ToolRegistry

from app.graph.nodes.router_node import router_node
from app.graph.nodes.planner_node import planner_node
from app.graph.nodes.memory_node import make_memory_node
from app.graph.nodes.retrieval_node import make_retrieval_node
from app.graph.nodes.tool_node import make_tool_node
from app.graph.nodes.context_node import context_node
from app.graph.nodes.response_node import make_response_node
from app.graph.nodes.validation_node import validation_node

logger = logging.getLogger(__name__)


def _should_run_tools(state: GraphState) -> str:
    """Conditional edge: route to Tool node or skip to Context."""
    tools = state.get("selected_tools", [])
    if tools:
        logger.info(f"Routing to ToolNode (tools={tools})")
        return "tool"
    logger.info("Skipping ToolNode → Context")
    return "context"


def build_chat_graph(
    services: ServiceContainer,
    tool_registry: ToolRegistry,
):
    """
    Construct and compile the Chat Graph.

    Returns a compiled LangGraph runnable.
    """
    # Create closured node functions
    memory_fn = make_memory_node(services)
    retrieval_fn = make_retrieval_node(services)
    tool_fn = make_tool_node(tool_registry)
    response_fn = make_response_node(services)

    # Build the graph
    graph = StateGraph(GraphState)

    graph.add_node("router", router_node)
    graph.add_node("planner", planner_node)
    graph.add_node("memory", memory_fn)
    graph.add_node("retrieval", retrieval_fn)
    graph.add_node("tool", tool_fn)
    graph.add_node("context", context_node)
    graph.add_node("response", response_fn)
    graph.add_node("validation", validation_node)

    # Edges
    graph.add_edge(START, "router")
    graph.add_edge("router", "planner")
    graph.add_edge("planner", "memory")
    graph.add_edge("memory", "retrieval")

    # Conditional: Tool or skip to Context
    graph.add_conditional_edges(
        "retrieval",
        _should_run_tools,
        {"tool": "tool", "context": "context"},
    )

    graph.add_edge("tool", "context")
    graph.add_edge("context", "response")
    graph.add_edge("response", "validation")
    graph.add_edge("validation", END)

    compiled = graph.compile()
    logger.info("ChatGraph compiled successfully.")
    return compiled
