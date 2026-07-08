from typing import List
import uuid
from app.services.retrieval.registry import BaseRetrievalStrategy, strategy_registry
from app.services.retrieval.models import QueryContext, RetrievedChunk
from app.services.vectorstore.qdrant_service import search

class SemanticStrategy(BaseRetrievalStrategy):
    @property
    def name(self) -> str:
        return "semantic"
        
    def retrieve(self, context: QueryContext) -> List[RetrievedChunk]:
        all_results = []
        exclude = context.filters.get("exclude_source")
        src_filter = context.filters.get("source")
        
        # We can execute search for each rewritten query and pool them
        queries = [context.raw_query] + context.rewritten_queries
        
        for q in queries:
            try:
                hits = search(query=q, limit=context.dynamic_top_k, source_filter=src_filter, exclude_source=exclude)
                for hit in hits:
                    chunk = RetrievedChunk(
                        id=str(uuid.uuid4()), # Need unique ID for chunk
                        text=hit.get("text", ""),
                        score=hit.get("score", 0.0),
                        source=hit.get("source", "unknown"),
                        repository=hit.get("repository", ""),
                        path=hit.get("path", ""),
                        url=hit.get("url", ""),
                        metadata=hit
                    )
                    all_results.append(chunk)
            except Exception:
                pass
                
        # Deduplicate by text to prevent same chunk from multiple queries
        seen = set()
        unique_results = []
        for chunk in sorted(all_results, key=lambda x: x.score, reverse=True):
            if chunk.text not in seen:
                seen.add(chunk.text)
                unique_results.append(chunk)
                
        return unique_results[:context.dynamic_top_k * 2]

strategy_registry.register(SemanticStrategy())
