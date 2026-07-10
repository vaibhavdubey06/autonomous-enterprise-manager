from typing import List
from app.services.retrieval.models import QueryContext, RetrievedChunk


class ContextOptimizer:
    def compress(
        self, chunks: List[RetrievedChunk], context: QueryContext
    ) -> List[RetrievedChunk]:
        """
        Optimize context by removing redundancy, maximizing evidence coverage,
        and staying within token budgets.
        """
        if not chunks:
            return []

        optimized = []
        seen_texts = set()

        # 1. Deduplication & Redundancy Removal
        for chunk in chunks:
            # Simple exact match or near-exact match deduplication
            # In a real enterprise system this could use minhash or dense vector clustering
            text_hash = hash(chunk.text.strip()[:100])  # hash first 100 chars
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                optimized.append(chunk)

        # 2. Enforce limits based on complexity to maximize token budget
        max_chunks = context.dynamic_top_k

        # 3. Ensure Diversity
        # We can sort chunks by source/repository to ensure not all chunks come from one document
        # if we have more than enough chunks.
        if len(optimized) > max_chunks:
            source_counts = {}
            diverse_chunks = []

            # First pass: try to get equal representation
            for chunk in optimized:
                src = chunk.metadata.get("document", "unknown")
                if (
                    source_counts.get(src, 0) < 3
                ):  # Max 3 chunks per document if diversifying
                    diverse_chunks.append(chunk)
                    source_counts[src] = source_counts.get(src, 0) + 1

            if len(diverse_chunks) < max_chunks:
                # fill remainder with top scored
                for chunk in optimized:
                    if chunk not in diverse_chunks:
                        diverse_chunks.append(chunk)
                    if len(diverse_chunks) == max_chunks:
                        break
            optimized = diverse_chunks[:max_chunks]

        return optimized
