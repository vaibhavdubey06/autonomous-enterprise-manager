"""Executive Decision Graph for approval and arbitration."""

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
        logger.info("ExecutiveDecisionGraph::%s — start", node_name)

        question = state.get("question", "")
        payload: dict[str, Any] = {
            "answer": f"{answer_prefix}: {question}".strip(),
            summary_key: {
                "question": question,
                "status": "evaluated",
            },
            "workflow_type": "executive_decision",
        }
        duration_ms = (time.perf_counter() - start) * 1000
        payload.update(_trace_step(state, node_name, start_ts, duration_ms))
        result: GraphState = cast(GraphState, {})
        result.update(state)
        result.update(payload)
        return result

    return _node


def build_executive_decision_graph(_services: ServiceContainer, _tool_registry):
    graph = StateGraph(GraphState)
    graph.add_node(
        "context",
        _build_node(
            "Context",
            "decision_context",
            "Decision context assembled",
        ),
    )
    graph.add_node(
        "options",
        _build_node("Options", "decision_options", "Options scored"),
    )
    graph.add_node(
        "governance",
        _build_node(
            "Governance",
            "decision_governance",
            "Governance reviewed",
        ),
    )
    graph.add_node(
        "decision",
        _build_node("Decision", "decision_result", "Executive decision"),
    )

    graph.add_edge(START, "context")
    graph.add_edge("context", "options")
    graph.add_edge("options", "governance")
    graph.add_edge("governance", "decision")
    graph.add_edge("decision", END)

    compiled = graph.compile()
    logger.info("ExecutiveDecisionGraph compiled successfully.")
    return compiled
