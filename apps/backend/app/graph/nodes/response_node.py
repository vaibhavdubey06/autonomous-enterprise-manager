"""
Response Node — Generates the final answer via LLMService.

Calls LLMService only.  Uses merged_context from state.
Saves the assistant response via MemoryService.
"""

import logging
import time
from datetime import datetime, timezone

from app.graph.state import GraphState
from app.graph.dependencies import ServiceContainer

logger = logging.getLogger(__name__)


def make_response_node(services: ServiceContainer):
    """Factory that closes over the ServiceContainer."""

    def response_node(state: GraphState) -> GraphState:
        start = time.perf_counter()
        start_ts = datetime.now(timezone.utc).isoformat()
        logger.info("ResponseNode — start")

        status = "success"
        answer = ""
        confidence = 0.0

        try:
            question = state.get("question", "")
            merged_context = state.get("merged_context", "")
            context_texts = state.get("context_texts", [])

            # Build the final prompt
            prompt = (
                "You are an enterprise assistant.\n"
                "Use the provided Conversation History and Context to answer the user's question.\n"
                "Do not invent information. If the answer cannot be found, say so.\n"
                "Always cite which retrieved chunks were used.\n\n"
                f"{merged_context}\n\n"
                f"Question: {question}"
            )

            # Call LLMService
            answer = services.llm_service.generate_answer(
                question=prompt,
                context=context_texts,
            )

            # Simple confidence heuristic: if we had sources, confidence is higher
            sources = state.get("sources", [])
            if sources:
                confidence = min(0.5 + len(sources) * 0.1, 1.0)
            else:
                confidence = 0.3

            # Persist assistant response in memory
            conversation_id = state.get("conversation_id")
            if conversation_id:
                services.memory_service.save_message(
                    conversation_id, "assistant", answer
                )

        except Exception:
            import traceback

            err_str = traceback.format_exc()
            logger.error(f"ResponseNode — error: {err_str}")
            with open(
                "C:/Users/dubey/autonomous-enterprise-manager/scratch_error.txt", "w"
            ) as f:
                f.write(err_str)
            answer = (
                "I encountered an error while generating a response. Please try again."
            )
            status = "error"

        duration_ms = (time.perf_counter() - start) * 1000
        end_ts = datetime.now(timezone.utc).isoformat()
        logger.info(f"ResponseNode — finish ({duration_ms:.1f}ms)")

        trace = list(state.get("execution_trace", []))
        trace.append(
            {
                "node": "Response",
                "start_time": start_ts,
                "end_time": end_ts,
                "duration_ms": round(duration_ms, 2),
                "status": status,
            }
        )

        metrics = state.get("metrics", {})
        metrics["llm_ms"] = round(duration_ms, 2)

        return {
            **state,
            "answer": answer,
            "confidence": confidence,
            "execution_trace": trace,
            "metrics": metrics,
        }

    return response_node
