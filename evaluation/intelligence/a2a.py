from typing import Dict, Any
from evaluation.models import EvaluationResult, ScoreModel

class A2AEvaluator:
    """
    Evaluator that assesses A2A integration.
    Calculates:
    - Discovery Accuracy
    - Delegation Success
    - Negotiation Success
    - Remote Reliability
    """
    
    def evaluate(self, result: EvaluationResult) -> Dict[str, float]:
        a2a_spans = [s for s in result.traces if "a2a_" in s.get("operation", "")]
        discovery = [s for s in a2a_spans if s.get("operation") == "a2a_discovery_request"]
        delegation = [s for s in a2a_spans if s.get("operation") == "a2a_delegation_request"]
        negotiation = [s for s in a2a_spans if s.get("operation") == "a2a_negotiation_request"]
        
        # Discovery Accuracy
        if discovery:
            success = sum(1 for s in discovery if s.get("status") == "SUCCESS")
            discovery_accuracy = success / len(discovery)
        else:
            discovery_accuracy = 1.0
            
        # Delegation Success
        if delegation:
            success = sum(1 for s in delegation if s.get("status") == "SUCCESS")
            delegation_success = success / len(delegation)
        else:
            delegation_success = 1.0
            
        # Negotiation Success
        if negotiation:
            success = sum(1 for s in negotiation if s.get("status") == "SUCCESS")
            negotiation_success = success / len(negotiation)
        else:
            negotiation_success = 1.0
            
        # Reliability (No errors in any A2A span)
        if a2a_spans:
            failures = sum(1 for s in a2a_spans if s.get("status") == "ERROR" or "error" in s.get("attributes", {}))
            reliability = max(0.0, 1.0 - (failures / len(a2a_spans)))
        else:
            reliability = 1.0
            
        return {
            "a2a_discovery_accuracy": discovery_accuracy,
            "a2a_delegation_success": delegation_success,
            "a2a_negotiation_success": negotiation_success,
            "a2a_reliability": reliability
        }
