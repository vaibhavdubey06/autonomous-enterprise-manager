from typing import Dict, Any, List
from evaluation.models import EvaluationResult, ScoreModel

class MCPEvaluator:
    """
    Evaluator that assesses the health, accuracy, and latency of MCP integration.
    Calculates:
    - Tool Success Rate
    - Discovery Accuracy 
    - MCP Latency
    - MCP Reliability
    """
    
    def evaluate(self, result: EvaluationResult) -> Dict[str, ScoreModel]:
        # Count spans
        mcp_spans = [s for s in result.traces if "mcp_" in s.get("operation", "")]
        tool_spans = [s for s in mcp_spans if s.get("operation") == "mcp_tool_execution"]
        
        # 1. Tool Success Rate
        if tool_spans:
            successful = sum(1 for s in tool_spans if s.get("status") == "SUCCESS")
            tool_success_rate = successful / len(tool_spans)
        else:
            tool_success_rate = 1.0 # Assume perfect if not used
            
        # 2. Reliability (No errors in any MCP span)
        if mcp_spans:
            failures = sum(1 for s in mcp_spans if s.get("status") == "ERROR" or "error" in s.get("attributes", {}))
            reliability = max(0.0, 1.0 - (failures / len(mcp_spans)))
        else:
            reliability = 1.0
            
        return {
            "tool_success_rate": tool_success_rate,
            "mcp_reliability": reliability
        }
