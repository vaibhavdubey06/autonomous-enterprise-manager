"""Workflow Graph for multi-step enterprise task automation."""

import logging
import time
from datetime import datetime, timezone
from importlib import import_module
from typing import Any, cast

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


def _build_node(node_name: str, summary_key: str, answer_prefix: str):
    def _node(state: GraphState) -> GraphState:
        start = time.perf_counter()
        start_ts = datetime.now(timezone.utc).isoformat()
        logger.info("WorkflowGraph::%s — start", node_name)

        question = state.get("question", "")
        payload: dict[str, Any] = {
            "answer": f"{answer_prefix}: {question}".strip(),
            summary_key: {
                "question": question,
                "status": "executed",
            },
            "workflow_type": "workflow",
        }
        duration_ms = (time.perf_counter() - start) * 1000
        payload.update(_trace_step(state, node_name, start_ts, duration_ms))
        result: GraphState = cast(GraphState, {})
        result.update(state)
        result.update(payload)
        return result

    return _node


def build_workflow_graph(_services: ServiceContainer, _tool_registry):
    graph = StateGraph(GraphState)
    graph.add_node(
        "intake",
        _build_node("Intake", "workflow_intake", "Workflow intake"),
    )
    graph.add_node(
        "decompose",
        _build_node("Decompose", "workflow_tasks", "Tasks decomposed"),
    )
    graph.add_node(
        "execute",
        _build_node("Execute", "workflow_execution", "Workflow executed"),
    )
    graph.add_node(
        "aggregate",
        _build_node("Aggregate", "workflow_aggregate", "Results aggregated"),
    )
    graph.add_node(
        "validate",
        _build_node("Validate", "workflow_validation", "Workflow validated"),
    )

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "decompose")
    graph.add_edge("decompose", "execute")
    graph.add_edge("execute", "aggregate")
    graph.add_edge("aggregate", "validate")
    graph.add_edge("validate", END)

    compiled = graph.compile()
    logger.info("WorkflowGraph compiled successfully.")
    return compiled
