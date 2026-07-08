"""Planning Graph for goal decomposition and plan generation."""

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
        logger.info("PlanningGraph::%s — start", node_name)

        question = state.get("question", "")
        payload: dict[str, Any] = {
            "answer": f"{answer_prefix}: {question}".strip(),
            summary_key: {
                "question": question,
                "status": "planned",
            },
            "workflow_type": "planning",
        }
        duration_ms = (time.perf_counter() - start) * 1000
        payload.update(_trace_step(state, node_name, start_ts, duration_ms))
        result: GraphState = cast(GraphState, {})
        result.update(state)
        result.update(payload)
        return result

    return _node


def build_planning_graph(_services: ServiceContainer, _tool_registry):
    graph = StateGraph(GraphState)
    graph.add_node(
        "goal_analysis",
        _build_node("GoalAnalysis", "planning_goal", "Goal analyzed"),
    )
    graph.add_node(
        "constraint_check",
        _build_node(
            "ConstraintCheck",
            "planning_constraints",
            "Constraints checked",
        ),
    )
    graph.add_node(
        "plan_generation",
        _build_node("PlanGeneration", "planning_plan", "Plan generated"),
    )
    graph.add_node(
        "validation",
        _build_node("Validation", "planning_validation", "Plan validated"),
    )

    graph.add_edge(START, "goal_analysis")
    graph.add_edge("goal_analysis", "constraint_check")
    graph.add_edge("constraint_check", "plan_generation")
    graph.add_edge("plan_generation", "validation")
    graph.add_edge("validation", END)

    compiled = graph.compile()
    logger.info("PlanningGraph compiled successfully.")
    return compiled
