"""
Memory Node — Orchestrates MemoryService to populate memory state.

Calls MemoryService only.  Never touches PostgreSQL or Qdrant directly.
"""

import logging
import time
from datetime import datetime, timezone

from app.graph.state import GraphState
from app.graph.dependencies import ServiceContainer

logger = logging.getLogger(__name__)


def make_memory_node(services: ServiceContainer):
    """
    Factory that closes over the ServiceContainer.
    Returns a node function compatible with LangGraph.
    """

    def memory_node(state: GraphState) -> GraphState:
        start = time.perf_counter()
        start_ts = datetime.now(timezone.utc).isoformat()
        logger.info("MemoryNode — start")

        status = "success"
        recent_memory = []
        semantic_memory = []
        memory_context = ""

        try:
            ms = services.memory_service
            question = state.get("question", "")

            # Ensure session & conversation exist
            session_id = ms.get_or_create_session(state.get("session_id"))
            conversation_id = ms.get_or_create_conversation(
                session_id, state.get("conversation_id")
            )

            # Persist the user message
            ms.save_message(conversation_id, "user", question)

            # Load recent history (always — cheap DB call)
            recent_memory = ms.get_recent_messages(conversation_id)

            # Semantic memory only when planner says so
            plan = state.get("plan", {})
            if plan.get("needs_memory", False):
                semantic_memory = ms.retrieve_semantic_memory(question)

            # Build working-memory prompt prefix
            memory_context = ms.build_memory_context(conversation_id)

            logger.info(
                f"MemoryNode — recent={len(recent_memory)}, "
                f"semantic={len(semantic_memory)}"
            )

        except Exception as e:
            logger.error(f"MemoryNode — error: {e}")
            status = "error"

        duration_ms = (time.perf_counter() - start) * 1000
        end_ts = datetime.now(timezone.utc).isoformat()
        logger.info(f"MemoryNode — finish ({duration_ms:.1f}ms)")

        trace = list(state.get("execution_trace", []))
        trace.append(
            {
                "node": "Memory",
                "start_time": start_ts,
                "end_time": end_ts,
                "duration_ms": round(duration_ms, 2),
                "status": status,
            }
        )

        metrics = state.get("metrics", {})
        metrics["memory_ms"] = round(duration_ms, 2)

        return {
            **state,
            "session_id": (
                session_id if status == "success" else state.get("session_id")
            ),
            "conversation_id": (
                conversation_id if status == "success" else state.get("conversation_id")
            ),
            "recent_memory": recent_memory,
            "semantic_memory": semantic_memory,
            "memory_context": memory_context,
            "execution_trace": trace,
            "metrics": metrics,
        }

    return memory_node
