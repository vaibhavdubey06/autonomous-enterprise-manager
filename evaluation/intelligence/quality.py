from evaluation.models import EvaluationResult
from evaluation.intelligence.utils import compute_semantic_similarity, extract_citations

class QualityEvaluator:
    def evaluate(self, result: EvaluationResult) -> dict:
        answer = result.actual_answer or ""
        ground_truth = result.ground_truth or ""
        
        # 1. Answer Relevance (Semantic + Deterministic check)
        # Deterministic: Does the answer contain expected key phrases from ground truth?
        # A simple deterministic approach: do they share significant words?
        ans_words = set(answer.lower().split())
        gt_words = set(ground_truth.lower().split())
        if gt_words:
            overlap = len(ans_words.intersection(gt_words)) / len(gt_words)
        else:
            overlap = 0.0
            
        semantic_sim = compute_semantic_similarity(answer, ground_truth)
        
        # Blended relevance score
        answer_relevance = (overlap * 0.3) + (semantic_sim * 0.7)
        
        # 2. Citation Accuracy
        citations = extract_citations(answer)
        citation_accuracy = 1.0 if citations else 0.0 # binary metric for now
        
        # 3. Groundedness / Faithfulness
        # Requires tracing what was retrieved. 
        # We will scan the traces for retrieved chunks and compute similarity.
        retrieved_texts = []
        for span in result.traces:
            if "search" in span.get("operation", "").lower() or "rag" in span.get("operation", "").lower():
                attrs = span.get("attributes", {})
                chunks = attrs.get("chunks", [])
                if chunks and isinstance(chunks, list):
                    for c in chunks:
                        if isinstance(c, dict) and "text" in c:
                            retrieved_texts.append(c["text"])
                            
        if retrieved_texts:
            # How semantically similar is the answer to the combined retrieved text?
            combined_context = " ".join(retrieved_texts)
            groundedness = compute_semantic_similarity(answer, combined_context)
            faithfulness = groundedness # tightly correlated
        else:
            groundedness = 0.0
            faithfulness = 0.0
            
        return {
            "answer_relevance": answer_relevance,
            "citation_accuracy": citation_accuracy,
            "groundedness": groundedness,
            "faithfulness": faithfulness
        }
