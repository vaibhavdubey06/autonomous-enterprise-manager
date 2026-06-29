"""
Validation Node — Final gate before returning to the user.

Verifies answer quality, source alignment, and confidence.
Produces a graceful fallback if anything is missing.
"""

import logging
import time
from datetime import datetime, timezone

from app.graph.state import GraphState

logger = logging.getLogger(__name__)

_FALLBACK_ANSWER = (
    "I was unable to generate a confident answer based on the available information. "
    "Please try rephrasing your question or provide more context."
)


def validation_node(state: GraphState) -> GraphState:
    """Pure function — no service dependencies needed."""
    start = time.perf_counter()
    start_ts = datetime.now(timezone.utc).isoformat()
    logger.info("ValidationNode — start")

    answer = state.get("answer", "")
    sources = state.get("sources", [])
    confidence = state.get("confidence", 0.0)
    requires_human = False
    status = "success"

    issues = []

    # ── Check 1: answer exists ──
    if not answer or not answer.strip():
        issues.append("answer is empty")

    # ── Check 2: sources exist when retrieval was performed ──
    plan = state.get("plan", {})
    if plan.get("needs_retrieval", False) and not sources:
        issues.append("retrieval was performed but no sources returned")

    # ── Check 3: confidence threshold ──
    if confidence < 0.3:
        issues.append(f"confidence too low ({confidence:.2f})")

    # ── Apply fallback if needed ──
    if issues:
        logger.warning(f"ValidationNode — issues detected: {issues}")
        if not answer or not answer.strip():
            answer = _FALLBACK_ANSWER
        requires_human = True
        status = "fallback"

    duration_ms = (time.perf_counter() - start) * 1000
    end_ts = datetime.now(timezone.utc).isoformat()
    logger.info(f"ValidationNode — finish ({duration_ms:.1f}ms), status={status}")

    trace = list(state.get("execution_trace", []))
    trace.append(
        {
            "node": "Validation",
            "start_time": start_ts,
            "end_time": end_ts,
            "duration_ms": round(duration_ms, 2),
            "status": status,
        }
    )

    metrics = dict(state.get("metrics", {}))
    metrics["validation_ms"] = round(duration_ms, 2)

    # Compute total_ms
    total_ms = sum(step.get("duration_ms", 0) for step in trace)
    metrics["total_ms"] = round(total_ms, 2)

    return {
        **state,
        "answer": answer,
        "requires_human": requires_human,
        "execution_trace": trace,
        "metrics": metrics,
    }
