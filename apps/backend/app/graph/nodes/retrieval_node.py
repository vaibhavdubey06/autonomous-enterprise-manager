"""
Retrieval Node — Orchestrates Qdrant search + Cross-Encoder reranking.

Calls qdrant_service.search() and CrossEncoderService only.
Never generates embeddings or queries the DB directly.
"""

import logging
import time
from datetime import datetime, timezone

from app.core.config import settings
from app.services.vectorstore.qdrant_service import search
from app.graph.state import GraphState
from app.graph.dependencies import ServiceContainer

logger = logging.getLogger(__name__)


def make_retrieval_node(services: ServiceContainer):
    """Factory that closes over the ServiceContainer."""

    def retrieval_node(state: GraphState) -> GraphState:
        start = time.perf_counter()
        start_ts = datetime.now(timezone.utc).isoformat()
        logger.info("RetrievalNode — start")

        status = "success"
        enterprise_context = []
        reranked_chunks = []

        plan = state.get("plan", {})

        if not plan.get("needs_retrieval", True):
            logger.info("RetrievalNode — skipped (planner said no retrieval needed)")
            status = "skipped"
        else:
            try:
                question = state.get("question", "")

                # Enterprise knowledge (exclude conversation memory)
                enterprise_context = search(
                    query=question,
                    limit=settings.QDRANT_TOP_K,
                    exclude_source="conversation",
                )
                logger.info(
                    f"RetrievalNode — enterprise chunks: {len(enterprise_context)}"
                )

                # Merge with semantic memory already in state
                semantic_memory = state.get("semantic_memory", [])
                candidate_pool = semantic_memory + enterprise_context

                # Rerank the merged pool
                if candidate_pool:
                    rerank_start = time.perf_counter()
                    reranked_chunks = services.cross_encoder_service.rerank_chunks(
                        query=question,
                        chunks=candidate_pool,
                        top_k=settings.RERANK_TOP_K,
                    )
                    rerank_ms = (time.perf_counter() - rerank_start) * 1000
                    metrics_update = {"rerank_ms": round(rerank_ms, 2)}
                    logger.info(
                        f"RetrievalNode — reranked to {len(reranked_chunks)} chunks in {rerank_ms:.1f}ms"
                    )
                else:
                    metrics_update = {}
                    logger.info("RetrievalNode — no candidates to rerank")

            except Exception as e:
                logger.error(f"RetrievalNode — error: {e}")
                status = "error"
                metrics_update = {}

        duration_ms = (time.perf_counter() - start) * 1000
        end_ts = datetime.now(timezone.utc).isoformat()
        logger.info(f"RetrievalNode — finish ({duration_ms:.1f}ms)")

        trace = list(state.get("execution_trace", []))
        trace.append(
            {
                "node": "Retrieval",
                "start_time": start_ts,
                "end_time": end_ts,
                "duration_ms": round(duration_ms, 2),
                "status": status,
            }
        )

        metrics = dict(state.get("metrics", {}))
        metrics["retrieval_ms"] = round(duration_ms, 2)
        if status == "success":
            metrics.update(metrics_update)

        return {
            **state,
            "enterprise_context": enterprise_context,
            "retrieved_chunks": enterprise_context,
            "reranked_chunks": reranked_chunks,
            "execution_trace": trace,
            "metrics": metrics,
        }

    return retrieval_node
