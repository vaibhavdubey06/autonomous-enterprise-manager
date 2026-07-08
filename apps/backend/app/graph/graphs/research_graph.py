"""Research Graph for evidence gathering and synthesis."""

import logging
import time
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

from app.graph.dependencies import ServiceContainer
from app.graph.state import GraphState

logger = logging.getLogger(__name__)

_langgraph = import_module("langgraph.graph")
END = _langgraph.END
START = _langgraph.START
StateGraph = _langgraph.StateGraph


def _trace_step(
    state: GraphState,
    node: str,
    start_ts: str,
    duration_ms: float,
    status: str = "success",
) -> dict:
    trace = list(state.get("execution_trace", []))
    trace.append(
        {
            "node": node,
            "start_time": start_ts,
            "end_time": datetime.now(timezone.utc).isoformat(),
            "duration_ms": round(duration_ms, 2),
            "status": status,
        }
    )
    metrics = dict(state.get("metrics", {}))
    metrics[f"{node.lower()}_ms"] = round(duration_ms, 2)
    return {"execution_trace": trace, "metrics": metrics}


def _build_node(node_name: str, answer_prefix: str):
    def _node(state: GraphState) -> GraphState:
        start = time.perf_counter()
        start_ts = datetime.now(timezone.utc).isoformat()
        logger.info("ResearchGraph::%s — start", node_name)

        question = state.get("question", "")
        payload: dict[str, Any] = {
            "answer": f"{answer_prefix}: {question}".strip(),
            "workflow_type": "research",
        }
        duration_ms = (time.perf_counter() - start) * 1000
        payload.update(_trace_step(state, node_name, start_ts, duration_ms))
        result: GraphState = {
            **state,
            "answer": payload["answer"],
            "workflow_type": payload["workflow_type"],
            "execution_trace": payload["execution_trace"],
            "metrics": payload["metrics"],
        }
        return result

    return _node


def build_research_graph(_services: ServiceContainer, _tool_registry):
    graph = StateGraph(GraphState)
    graph.add_node(
        "frame",
        _build_node("Frame", "Research frame"),
    )
    graph.add_node(
        "plan_sources",
        _build_node("PlanSources", "Sources planned"),
    )
    graph.add_node(
        "retrieve",
        _build_node("Retrieve", "Evidence retrieved"),
    )
    graph.add_node(
        "synthesize",
        _build_node("Synthesize", "Research synthesis"),
    )
    graph.add_node(
        "validate",
        _build_node("Validate", "Research validated"),
    )

    graph.add_edge(START, "frame")
    graph.add_edge("frame", "plan_sources")
    graph.add_edge("plan_sources", "retrieve")
    graph.add_edge("retrieve", "synthesize")
    graph.add_edge("synthesize", "validate")
    graph.add_edge("validate", END)

    compiled = graph.compile()
    logger.info("ResearchGraph compiled successfully.")
    return compiled
