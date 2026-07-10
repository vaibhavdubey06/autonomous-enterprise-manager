import logging
from typing import Dict, Any
from app.services.decisions.models import DecisionType, DecisionRecord

logger = logging.getLogger(__name__)


class DecisionPolicies:
    """Configurable rules governing decisions."""

    # Defaults. In a real system these could be loaded from a DB or YAML.
    POLICIES = {
        DecisionType.PLANNING: {"min_confidence": 0.6, "max_risk": 0.8},
        DecisionType.ROUTING: {
            "min_confidence": 0.4,
            "max_risk": 0.9,
            "max_cost": 2.0,
            "max_latency": 5000,
        },
        DecisionType.RETRIEVAL: {"min_confidence": 0.5, "max_risk": 1.0},
        DecisionType.RECOVERY: {"min_confidence": 0.3, "max_risk": 0.7},
        DecisionType.CAPABILITY: {"min_confidence": 0.5, "max_risk": 0.8},
    }

    @classmethod
    def evaluate(cls, record: DecisionRecord) -> Dict[str, Any]:
        """Evaluates a decision against policies."""
        policy = cls.POLICIES.get(record.decision_type, {})

        reasons = []
        is_compliant = True

        min_conf = policy.get("min_confidence", 0.0)
        if record.confidence < min_conf:
            is_compliant = False
            reasons.append(
                f"Confidence {record.confidence:.2f} below threshold {min_conf:.2f}"
            )

        max_risk = policy.get("max_risk", 1.0)
        if record.risk > max_risk:
            is_compliant = False
            reasons.append(f"Risk {record.risk:.2f} above threshold {max_risk:.2f}")

        if record.decision_type == DecisionType.ROUTING:
            max_cost = policy.get("max_cost", 10.0)
            if record.cost > max_cost:
                is_compliant = False
                reasons.append(f"Cost {record.cost} above threshold {max_cost}")

            max_lat = policy.get("max_latency", 10000)
            if record.latency_ms > max_lat:
                is_compliant = False
                reasons.append(f"Latency {record.latency_ms} above threshold {max_lat}")

        return {"compliant": is_compliant, "violations": reasons}
