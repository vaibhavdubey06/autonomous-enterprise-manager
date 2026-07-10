from typing import Dict, Any
from app.services.decisions.models import DecisionType


class ConfidenceEngine:
    """Calculates multi-signal confidence scores for decisions."""

    @classmethod
    def calculate(cls, decision_type: DecisionType, context: Dict[str, Any]) -> float:
        if decision_type == DecisionType.PLANNING:
            return cls._calc_planning(context)
        elif decision_type == DecisionType.ROUTING:
            return cls._calc_routing(context)
        elif decision_type == DecisionType.RETRIEVAL:
            return cls._calc_retrieval(context)
        elif decision_type == DecisionType.RECOVERY:
            return cls._calc_recovery(context)
        elif decision_type == DecisionType.CAPABILITY:
            return cls._calc_capability(context)
        return 0.5

    @classmethod
    def _calc_planning(cls, context: Dict[str, Any]) -> float:
        # e.g., template match (+0.3), historical success (+0.4)
        score = 0.5
        if context.get("template_used"):
            score += 0.3
        hist = context.get("historical_success", 0.5)
        score = (score + hist) / 2
        return min(1.0, max(0.0, score))

    @classmethod
    def _calc_routing(cls, context: Dict[str, Any]) -> float:
        # health_score is 0-1
        health = context.get("health_score", 0.5)
        hist = context.get("historical_success", 0.8)
        lat_class = context.get("latency_class", "medium")
        lat_bonus = (
            0.1 if lat_class == "fast" else (-0.1 if lat_class == "slow" else 0.0)
        )

        score = (health * 0.6) + (hist * 0.4) + lat_bonus
        return min(1.0, max(0.0, score))

    @classmethod
    def _calc_retrieval(cls, context: Dict[str, Any]) -> float:
        # e.g., based on hybrid score vs semantic
        strategy = context.get("strategy", "semantic")
        if strategy == "hybrid":
            return 0.85
        elif strategy == "semantic":
            return 0.70
        return 0.60

    @classmethod
    def _calc_recovery(cls, context: Dict[str, Any]) -> float:
        cycles = context.get("recovery_cycles", 0)
        base = 0.9
        # Confidence drops as recovery cycles increase
        score = base - (cycles * 0.15)
        return min(1.0, max(0.0, score))

    @classmethod
    def _calc_capability(cls, context: Dict[str, Any]) -> float:
        # Base LLM confidence
        llm_conf = context.get("llm_confidence", 0.5)
        hist = context.get("historical_success", 0.5)

        score = (llm_conf * 0.7) + (hist * 0.3)
        return min(1.0, max(0.0, score))
