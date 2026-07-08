from evaluation.models import EvaluationResult

class MemoryEvaluator:
    def evaluate(self, result: EvaluationResult) -> dict:
        memory_utilization = 0.0
        reflection_quality = 0.0
        
        for span in result.traces:
            op = span.get("operation", "").lower()
            if "memory" in op:
                memory_utilization = 1.0
            if "reflection" in op:
                reflection_quality = 1.0
                
        return {
            "memory_utilization": memory_utilization,
            "reflection_quality": reflection_quality
        }
