from typing import Dict, Any
from app.services.decisions.models import DecisionType, Explanation


class ExplainabilityEngine:
    """Generates structured explanations for decisions."""

    @classmethod
    def explain(
        cls, decision_type: DecisionType, selected_option: str, context: Dict[str, Any]
    ) -> Explanation:
        if decision_type == DecisionType.PLANNING:
            return cls._explain_planning(selected_option, context)
        elif decision_type == DecisionType.ROUTING:
            return cls._explain_routing(selected_option, context)
        elif decision_type == DecisionType.RETRIEVAL:
            return cls._explain_retrieval(selected_option, context)
        elif decision_type == DecisionType.RECOVERY:
            return cls._explain_recovery(selected_option, context)
        elif decision_type == DecisionType.CAPABILITY:
            return cls._explain_capability(selected_option, context)

        return Explanation(summary=f"Selected {selected_option}", factors=[])

    @classmethod
    def _explain_planning(cls, option: str, context: Dict[str, Any]) -> Explanation:
        template = context.get("template_used")
        factors = []
        if template:
            factors.append(
                f"Matched workflow template '{template}' based on user goal."
            )
        factors.append(
            f"Plan complexity estimated at {context.get('complexity', 'unknown')}."
        )
        return Explanation(
            summary=f"Formulated strategic plan: {option}", factors=factors
        )

    @classmethod
    def _explain_routing(cls, option: str, context: Dict[str, Any]) -> Explanation:
        factors = [
            f"Provider Health: {context.get('health_score', 'N/A')}",
            f"Latency Profile: {context.get('latency_class', 'N/A')}",
        ]
        if context.get("capability_match"):
            factors.append("Strong capability match for request payload.")
        return Explanation(
            summary=f"Routed request to provider {option}", factors=factors
        )

    @classmethod
    def _explain_retrieval(cls, option: str, context: Dict[str, Any]) -> Explanation:
        factors = [
            f"Query complexity inferred as {context.get('query_type', 'semantic')}",
            f"Available documents: {context.get('docs_available', 'unknown')}",
        ]
        return Explanation(
            summary=f"Selected {option} retrieval strategy", factors=factors
        )

    @classmethod
    def _explain_recovery(cls, option: str, context: Dict[str, Any]) -> Explanation:
        factors = [
            f"Triggering failure: {context.get('failure_reason', 'unknown')}",
            f"Current recovery cycles: {context.get('recovery_cycles', 0)}",
        ]
        return Explanation(
            summary=f"Attempting {option} to recover workflow", factors=factors
        )

    @classmethod
    def _explain_capability(cls, option: str, context: Dict[str, Any]) -> Explanation:
        factors = ["Inferred intent matches capability requirements."]
        if context.get("historical_success"):
            factors.append(
                "High historical success rate for this capability on similar tasks."
            )
        return Explanation(summary=f"Selected capability {option}", factors=factors)
