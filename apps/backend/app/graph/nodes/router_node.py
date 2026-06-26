"""
Router Node — Entry point that determines which graph should execute.

Currently routes everything to ChatGraph.
Future graphs (Research, Workflow, Planning) plug in without modifying this node.
"""

import logging
import time
from datetime import datetime, timezone

from app.graph.state import GraphState

logger = logging.getLogger(__name__)


def router_node(state: GraphState) -> GraphState:
    """
    Classify the user's intent and select a workflow type.

    Currently all requests are routed to the 'chat' workflow.
    """
    start = time.perf_counter()
    start_ts = datetime.now(timezone.utc).isoformat()
    logger.info("RouterNode — start")

    question = state.get("question", "")

    # ── Deterministic intent classification ──
    # Future: use a lightweight classifier or keyword heuristics
    # to route to research / workflow / planning graphs.
    user_intent = "chat"
    workflow_type = "chat"

    duration_ms = (time.perf_counter() - start) * 1000
    end_ts = datetime.now(timezone.utc).isoformat()
    logger.info(f"RouterNode — finish ({duration_ms:.1f}ms) → workflow_type={workflow_type}")

    trace = list(state.get("execution_trace", []))
    trace.append({
        "node": "Router",
        "start_time": start_ts,
        "end_time": end_ts,
        "duration_ms": round(duration_ms, 2),
        "status": "success",
    })

    metrics = dict(state.get("metrics", {}))
    metrics["router_ms"] = round(duration_ms, 2)

    return {
        **state,
        "user_intent": user_intent,
        "workflow_type": workflow_type,
        "execution_trace": trace,
        "metrics": metrics,
    }
