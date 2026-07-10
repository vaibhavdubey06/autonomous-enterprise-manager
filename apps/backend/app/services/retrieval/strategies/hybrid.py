from typing import List, Dict
from app.services.retrieval.registry import BaseRetrievalStrategy, strategy_registry
from app.services.retrieval.models import QueryContext, RetrievedChunk
from .semantic import SemanticStrategy
from .keyword import KeywordStrategy


class HybridStrategy(BaseRetrievalStrategy):
    @property
    def name(self) -> str:
        return "hybrid"

    def _compute_rrf(
        self,
        semantic_chunks: List[RetrievedChunk],
        keyword_chunks: List[RetrievedChunk],
        k: int = 60,
    ) -> List[RetrievedChunk]:
        """Reciprocal Rank Fusion"""
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, RetrievedChunk] = {}

        # Process semantic ranks
        for rank, chunk in enumerate(semantic_chunks):
            chunk_hash = chunk.text
            if chunk_hash not in rrf_scores:
                rrf_scores[chunk_hash] = 0.0
                chunk_map[chunk_hash] = chunk
            rrf_scores[chunk_hash] += 1.0 / (k + rank + 1)

        # Process keyword ranks
        for rank, chunk in enumerate(keyword_chunks):
            chunk_hash = chunk.text
            if chunk_hash not in rrf_scores:
                rrf_scores[chunk_hash] = 0.0
                chunk_map[chunk_hash] = chunk
            # Give keyword hits a slight weight boost if they matched exactly
            rrf_scores[chunk_hash] += 1.5 / (k + rank + 1)

        # Re-score and sort
        fused = []
        for chunk_hash, score in sorted(
            rrf_scores.items(), key=lambda x: x[1], reverse=True
        ):
            chunk = chunk_map[chunk_hash]
            chunk.score = score
            fused.append(chunk)

        return fused

    def retrieve(self, context: QueryContext) -> List[RetrievedChunk]:
        semantic = SemanticStrategy()
        keyword = KeywordStrategy()

        semantic_results = semantic.retrieve(context)
        keyword_results = keyword.retrieve(context)

        # Fuse
        fused_results = self._compute_rrf(semantic_results, keyword_results)

        return fused_results[: context.dynamic_top_k * 2]


strategy_registry.register(HybridStrategy())
