"""
Retrieval Node — Orchestrates enterprise retrieval using RetrievalEngine.

Calls RetrievalEngine.retrieve() directly.
The orchestration belongs inside RetrievalEngine not inside LangGraph.
"""

import logging
import time
from datetime import datetime, timezone

from app.graph.state import GraphState
from app.graph.dependencies import ServiceContainer
from app.services.retrieval import RetrievalEngine
from app.services.retrieval.components import (
    QueryAnalyzer,
    QueryRewriter,
    ContextOptimizer,
    CitationBuilder,
)

logger = logging.getLogger(__name__)

# We instantiate the engine here or it could be injected via ServiceContainer.
# For simplicity, we can build it here since components are stateless.
engine = RetrievalEngine(
    analyzer=QueryAnalyzer(),
    rewriter=QueryRewriter(),
    compressor=ContextOptimizer(),
    citation_builder=CitationBuilder(),
    reranker_service=None,  # Will be injected below
)


def make_retrieval_node(services: ServiceContainer):
    """Factory that closes over the ServiceContainer."""
    # Inject cross_encoder_service into engine
    engine.reranker_service = services.cross_encoder_service

    def retrieval_node(state: GraphState) -> GraphState:
        start = time.perf_counter()
        start_ts = datetime.now(timezone.utc).isoformat()
        logger.info("RetrievalNode — start")

        status = "success"
        enterprise_context = []

        plan = state.get("plan", {})

        if not plan.get("needs_retrieval", True):
            logger.info("RetrievalNode — skipped (planner said no retrieval needed)")
            status = "skipped"
        else:
            try:
                question = state.get("question", "")

                # Use RetrievalEngine to fetch optimized and cited chunks
                filters = {"exclude_source": "conversation"}
                retrieval_result = engine.retrieve(query=question, filters=filters)

                # Convert back to standard dict list for backwards compatibility
                enterprise_context = [
                    {
                        "score": c.score,
                        "document": c.metadata.get("document", ""),
                        "page": c.metadata.get("page", 1),
                        "chunk": c.metadata.get("chunk", 0),
                        "text": c.text,
                        "source": c.source,
                        "repository": c.repository,
                        "path": c.metadata.get("path", ""),
                        "url": c.metadata.get("url", ""),
                        "citation": c.citation,
                    }
                    for c in retrieval_result.chunks
                ]

                logger.info(
                    f"RetrievalNode — engine retrieved {len(enterprise_context)} chunks using {retrieval_result.strategy_used}"
                )

            except Exception as e:
                logger.error(f"RetrievalNode — error: {e}")
                status = "error"

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

        metrics = state.get("metrics", {})
        metrics["retrieval_ms"] = round(duration_ms, 2)

        return {
            **state,
            "enterprise_context": enterprise_context,
            "retrieved_chunks": enterprise_context,
            "reranked_chunks": enterprise_context,  # Now identical since Engine handles reranking
            "execution_trace": trace,
            "metrics": metrics,
        }

    return retrieval_node
