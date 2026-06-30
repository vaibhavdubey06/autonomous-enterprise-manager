"""
Context Node — Merges all retrieved context into a normalised prompt.

Delegates to context_builder.build_merged_context().
Response Node should NOT merge context — it only generates.
"""

import logging
import time
from datetime import datetime, timezone

from app.graph.state import GraphState
from app.graph.context_builder import build_merged_context

logger = logging.getLogger(__name__)


def context_node(state: GraphState) -> GraphState:
    """
    Pure function — no service dependencies needed.
    Reads reranked_chunks, memory_context, tool_results from state.
    Writes merged_context, context_texts, sources.
    """
    start = time.perf_counter()
    start_ts = datetime.now(timezone.utc).isoformat()
    logger.info("ContextNode — start")

    status = "success"
    try:
        merged_context, context_texts, sources = build_merged_context(
            memory_context=state.get("memory_context", ""),
            reranked_chunks=state.get("reranked_chunks", []),
            tool_results=state.get("tool_results", []),
        )
    except Exception as e:
        logger.error(f"ContextNode — error: {e}")
        merged_context = ""
        context_texts = []
        sources = []
        status = "error"

    duration_ms = (time.perf_counter() - start) * 1000
    end_ts = datetime.now(timezone.utc).isoformat()
    logger.info(f"ContextNode — finish ({duration_ms:.1f}ms)")

    trace = list(state.get("execution_trace", []))
    trace.append(
        {
            "node": "Context",
            "start_time": start_ts,
            "end_time": end_ts,
            "duration_ms": round(duration_ms, 2),
            "status": status,
        }
    )

    metrics = state.get("metrics", {})
    metrics["context_ms"] = round(duration_ms, 2)

    return {
        **state,
        "merged_context": merged_context,
        "context_texts": context_texts,
        "sources": sources,
        "execution_trace": trace,
        "metrics": metrics,
    }
