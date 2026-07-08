from evaluation.models import EvaluationResult

class CapabilityEvaluator:
    def evaluate(self, result: EvaluationResult) -> dict:
        selected_agent = "unknown"
        for span in result.traces:
            if span.get("operation", "") == "agent_routing":
                selected_agent = span.get("attributes", {}).get("selected_agent", "unknown")
                
        capability_accuracy = 1.0 if result.expected_capability in selected_agent else 0.0
        agent_accuracy = 1.0 if selected_agent == result.expected_agent else 0.0
        
        return {
            "capability_inference_accuracy": capability_accuracy,
            "agent_selection_accuracy": agent_accuracy
        }
