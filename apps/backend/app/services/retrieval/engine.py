import time
import logging
from typing import Dict, Any, Optional

from app.services.retrieval.models import QueryContext, RetrievalResult
from app.services.retrieval.registry import strategy_registry
from app.operations.tracing.trace_manager import TraceManager
from app.operations.telemetry.telemetry_context import TelemetryContext

logger = logging.getLogger(__name__)

class RetrievalEngine:
    def __init__(self, analyzer, rewriter, compressor, citation_builder, reranker_service, decision_engine=None):
        self.analyzer = analyzer
        self.rewriter = rewriter
        self.compressor = compressor
        self.citation_builder = citation_builder
        self.reranker_service = reranker_service
        self.trace_manager = TraceManager()
        from app.services.decisions.engine import DecisionEngine
        self.decision_engine = decision_engine or DecisionEngine()
        
    def _select_strategy(self, context: QueryContext) -> str:
        # Default logic based on intent/complexity
        if context.intent == "code_search":
            return "keyword"
        return "hybrid"

    def retrieve(self, query: str, filters: Optional[Dict[str, Any]] = None) -> RetrievalResult:
        start_time = time.perf_counter()
        latencies = {}
        
        telemetry_snap = TelemetryContext.get_snapshot()
        trace_id = telemetry_snap.get("trace_id")
        parent_span_id = telemetry_snap.get("span_id")
        
        # If no active trace, create a dummy trace_id so span manager works locally
        if not trace_id:
            trace_id = "local_retrieval_trace"
            parent_span_id = None
            
        with self.trace_manager.span(trace_id, "retrieval_engine", parent_span_id) as main_span:
            try:
                # 1. Analyze
                with self.trace_manager.span(trace_id, "query_analysis", main_span.span_id) as span:
                    t0 = time.perf_counter()
                    context = self.analyzer.analyze(query, filters or {})
                    latencies["analysis"] = (time.perf_counter() - t0) * 1000
                    span.attributes.update({"intent": context.intent, "is_complex": context.is_complex})
                
                # 2. Rewrite
                with self.trace_manager.span(trace_id, "query_rewrite", main_span.span_id) as span:
                    t0 = time.perf_counter()
                    context = self.rewriter.rewrite(context)
                    latencies["rewrite"] = (time.perf_counter() - t0) * 1000
                    span.attributes.update({"rewritten_count": len(context.rewritten_queries)})
                
                # 3. Strategy
                with self.trace_manager.span(trace_id, "strategy_selection", main_span.span_id) as span:
                    strategy_name = self._select_strategy(context)
                    
                    from app.services.decisions.models import DecisionType
                    self.decision_engine.record_decision(
                        decision_type=DecisionType.RETRIEVAL,
                        component="RetrievalEngine",
                        selected_option=strategy_name,
                        context={"query_type": context.intent, "strategy": strategy_name},
                        trace_id=trace_id
                    )
                    
                    strategy = strategy_registry.get_strategy(strategy_name)
                    span.attributes.update({"strategy": strategy_name})
                
                # 4. Search & Fusion (internal to strategy)
                with self.trace_manager.span(trace_id, f"{strategy_name}_search", main_span.span_id) as span:
                    t0 = time.perf_counter()
                    raw_chunks = strategy.retrieve(context)
                    latencies["search_and_fusion"] = (time.perf_counter() - t0) * 1000
                    span.attributes.update({"retrieved_chunks": len(raw_chunks)})
                
                # 5. Rerank
                with self.trace_manager.span(trace_id, "reranking", main_span.span_id) as span:
                    t0 = time.perf_counter()
                    reranked_chunks = self.reranker_service.rerank_chunks(query, raw_chunks, top_k=context.dynamic_top_k * 2)
                    latencies["rerank"] = (time.perf_counter() - t0) * 1000
                
                # 6. Compress
                with self.trace_manager.span(trace_id, "compression", main_span.span_id) as span:
                    t0 = time.perf_counter()
                    optimized_chunks = self.compressor.compress(reranked_chunks, context)
                    latencies["compression"] = (time.perf_counter() - t0) * 1000
                    span.attributes.update({"discarded_chunks": len(raw_chunks) - len(optimized_chunks)})
                
                # 7. Citations
                with self.trace_manager.span(trace_id, "citation_generation", main_span.span_id) as span:
                    t0 = time.perf_counter()
                    final_chunks = self.citation_builder.build_citations(optimized_chunks)
                    latencies["citations"] = (time.perf_counter() - t0) * 1000
                
                latencies["total"] = (time.perf_counter() - start_time) * 1000
                
                main_span.attributes.update({
                    "strategy": strategy_name,
                    "fusion_latency": latencies.get("search_and_fusion", 0),
                    "compression_latency": latencies.get("compression", 0),
                    "chunks_retrieved": len(raw_chunks),
                    "chunks_discarded": len(raw_chunks) - len(final_chunks),
                    "dynamic_top_k": context.dynamic_top_k
                })
                
                return RetrievalResult(
                    chunks=final_chunks,
                    context=context,
                    strategy_used=strategy_name,
                    latency_ms=latencies,
                    metrics={
                        "raw_retrieved": len(raw_chunks),
                        "optimized_count": len(final_chunks),
                        "compression_ratio": len(final_chunks) / len(raw_chunks) if raw_chunks else 0
                    }
                )
            except Exception as e:
                raise e
