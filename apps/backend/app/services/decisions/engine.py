import logging
from typing import Dict, Any, Optional
from app.services.decisions.models import DecisionRecord, DecisionType
from app.services.decisions.confidence import ConfidenceEngine
from app.services.decisions.policies import DecisionPolicies
from app.services.decisions.explainability import ExplainabilityEngine
from app.operations.tracing.trace_manager import TraceManager

logger = logging.getLogger(__name__)

class DecisionEngine:
    """
    Cross-cutting orchestration layer for decisions.
    Records, calculates confidence, evaluates policies, explains, and emits telemetry.
    """
    
    def __init__(self):
        self.trace_manager = TraceManager()
        # In a real app we'd inject the workflow optimizer / memory store here 
        # to persist records. For now we rely on Reflection to pick them up from traces 
        # or we could push them to an in-memory list.
        self._recorded_decisions = []

    def record_decision(
        self,
        decision_type: DecisionType,
        component: str,
        selected_option: str,
        context: Dict[str, Any],
        alternative_options: Optional[list] = None,
        workflow_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        risk: float = 0.0,
        latency_ms: float = 0.0,
        cost: float = 0.0
    ) -> DecisionRecord:
        
        # 1. Calculate Confidence
        confidence = ConfidenceEngine.calculate(decision_type, context)
        
        # 2. Explain
        explanation = ExplainabilityEngine.explain(decision_type, selected_option, context)
        
        # 3. Create Record
        record = DecisionRecord(
            workflow_id=workflow_id,
            trace_id=trace_id,
            decision_type=decision_type,
            component=component,
            selected_option=selected_option,
            alternative_options=alternative_options or [],
            confidence=confidence,
            risk=risk,
            reasoning=explanation,
            latency_ms=latency_ms,
            cost=cost,
            context=context
        )
        
        # 4. Policy Evaluation (Just recording the result in telemetry)
        policy_eval = DecisionPolicies.evaluate(record)
        is_compliant = policy_eval["compliant"]
        
        if not is_compliant:
            logger.warning(f"Decision {record.decision_id} violated policies: {policy_eval['violations']}")
            
        # 5. Telemetry
        self._emit_telemetry(record, is_compliant)
        
        # 6. Store locally (would be sent to reflection memory)
        self._recorded_decisions.append(record)
        
        return record

    def _emit_telemetry(self, record: DecisionRecord, is_compliant: bool):
        # We start a span specifically for the decision
        span = self.trace_manager.start_span(
            trace_id=record.trace_id or "decision_trace",
            operation="decision_recorded",
            decision_type=record.decision_type.value,
            component=record.component,
            selected_option=record.selected_option,
            confidence=record.confidence,
            risk=record.risk,
            policy_compliant=is_compliant
        )
        self.trace_manager.end_span(span, "OK")
        
    def get_recent_decisions(self):
        return self._recorded_decisions

    def route_connector(self, capability: str, candidates: list) -> str:
        """
        Dynamically selects the best connector based on ConnectorProfile metrics
        such as health, cost, and rate limits. (Simulated heuristic for now).
        """
        if not candidates:
            raise ValueError("No connector candidates provided.")
            
        # In a real system, we fetch the ConnectorProfile for each candidate
        # and score them. Here we just simulate picking the first healthy one,
        # or prioritizing lower cost.
        selected = candidates[0]
        
        # Record the routing decision
        self.record_decision(
            decision_type=DecisionType.ROUTING,
            component="ConnectorManager",
            selected_option=selected,
            context={"capability": capability, "candidates": candidates},
            alternative_options=[c for c in candidates if c != selected],
            confidence=0.95
        )
        return selected
