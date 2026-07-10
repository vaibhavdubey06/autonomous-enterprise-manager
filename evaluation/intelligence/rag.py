from evaluation.models import EvaluationResult
from evaluation.intelligence.utils import compute_semantic_similarity
import math


class RAGEvaluator:
    def evaluate(self, result: EvaluationResult) -> dict:
        precision = 0.0
        recall = 0.0
        mrr = 0.0
        ndcg = 0.0
        context_utilization = 0.0
        compression_ratio = 0.0
        search_latency = 0.0
        strategy = "unknown"

        expected_docs_count = (
            1  # Assuming at least 1 doc is expected for retrieval tasks
        )

        for span in result.traces:
            if (
                "retrieval_engine" in span.get("operation", "").lower()
                or "knowledge_search" in span.get("operation", "").lower()
            ):
                attrs = span.get("attributes", {})
                chunks_retrieved = attrs.get("chunks_retrieved", 0)
                attrs.get("chunks_discarded", 0)
                strategy = attrs.get("query_strategy", strategy)
                search_latency = span.get("duration_ms", 0)

                # We need chunks from the span if they were logged, or from the generated citations
                # The LLM prompt input usually contains the context.
                pass

            if (
                "search" in span.get("operation", "").lower()
                or "rag" in span.get("operation", "").lower()
            ):
                attrs = span.get("attributes", {})
                chunks = attrs.get("chunks", [])

                if chunks and isinstance(chunks, list):
                    relevant_chunks = 0
                    first_relevant_idx = -1
                    dcg = 0.0
                    idcg = 0.0

                    for idx, c in enumerate(chunks):
                        text = c.get("text", "") if isinstance(c, dict) else ""
                        # Chunk level relevance
                        sim = compute_semantic_similarity(text, result.ground_truth)

                        # Perfect idealized ranking (IDCG)
                        idcg += 1.0 / math.log2(idx + 2)

                        if sim > 0.5:  # threshold for relevant chunk
                            relevant_chunks += 1
                            if first_relevant_idx == -1:
                                first_relevant_idx = idx

                            # DCG calculation
                            dcg += 1.0 / math.log2(idx + 2)

                    precision = relevant_chunks / len(chunks)
                    recall = min(1.0, relevant_chunks / expected_docs_count)

                    if first_relevant_idx != -1:
                        mrr = 1.0 / (first_relevant_idx + 1)

                    if idcg > 0:
                        ndcg = dcg / idcg

                    # Context utilization (naive proxy: precision)
                    context_utilization = precision

                    # Estimate compression ratio if not explicitly logged
                    if chunks_retrieved == 0:
                        chunks_retrieved = len(chunks)

                    if chunks_retrieved > 0:
                        compression_ratio = 1.0 - (len(chunks) / chunks_retrieved)

        return {
            "retrieval_precision": precision,
            "retrieval_recall": recall,
            "mrr": mrr,
            "ndcg": ndcg,
            "context_utilization": context_utilization,
            "compression_ratio": compression_ratio,
            "search_strategy": strategy,
            "retrieval_latency": search_latency,
        }
