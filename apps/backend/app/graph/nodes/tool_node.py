"""
Tool Node — Executes optional tools selected by the Planner.

Calls ToolRegistry only.  Never touches connectors directly.
"""

import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.graph.state import GraphState
from app.graph.registry import ToolRegistry

logger = logging.getLogger(__name__)


def make_tool_node(tool_registry: ToolRegistry):
    """Factory that closes over the ToolRegistry."""

    def tool_node(state: GraphState) -> GraphState:
        start = time.perf_counter()
        start_ts = datetime.now(timezone.utc).isoformat()
        logger.info("ToolNode — start")

        selected_tools: List[str] = state.get("selected_tools", [])
        tool_results: List[Dict[str, Any]] = list(state.get("tool_results", []))
        status = "success"

        if not selected_tools:
            logger.info("ToolNode — no tools selected, skipping")
            status = "skipped"
        else:
            for tool_name in selected_tools:
                logger.info(f"ToolNode — executing: {tool_name}")
                result = tool_registry.execute(tool_name, state)
                tool_results.append(result)

        duration_ms = (time.perf_counter() - start) * 1000
        end_ts = datetime.now(timezone.utc).isoformat()
        logger.info(
            f"ToolNode — finish ({duration_ms:.1f}ms), results={len(tool_results)}"
        )

        trace = list(state.get("execution_trace", []))
        trace.append(
            {
                "node": "Tool",
                "start_time": start_ts,
                "end_time": end_ts,
                "duration_ms": round(duration_ms, 2),
                "status": status,
            }
        )

        metrics = dict(state.get("metrics", {}))
        metrics["tool_ms"] = round(duration_ms, 2)

        return {
            **state,
            "tool_results": tool_results,
            "execution_trace": trace,
            "metrics": metrics,
        }

    return tool_node
