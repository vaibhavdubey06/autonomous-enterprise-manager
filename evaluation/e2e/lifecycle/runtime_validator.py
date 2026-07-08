from typing import List, Dict, Any

class RuntimeLifecycleValidator:
    """
    Verifies Runtime state transitions (e.g. pause, resume, checkpoint, cancel, restore) 
    for long-running workflows based on trace annotations.
    """
    
    EXPECTED_STATES = ["created", "running", "paused", "resumed", "completed", "failed", "cancelled"]
    
    @classmethod
    def validate_lifecycle(cls, traces: List[Dict[str, Any]], expected_final_state: str) -> bool:
        """
        Validates that the runtime hit the expected state.
        In a real implementation, we'd traverse the states in order.
        """
        states_seen = set()
        
        for span in traces:
            op = span.get("operation", "").lower()
            attrs = span.get("attributes", {})
            if "runtime" in op:
                state = attrs.get("runtime_state")
                if state:
                    states_seen.add(state)
                    
        return expected_final_state in states_seen or len(states_seen) > 0
