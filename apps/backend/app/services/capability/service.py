import logging
import re
from typing import Dict, Any, List

from app.services.capability.registry import CapabilityDecision, CAPABILITY_REGISTRY

logger = logging.getLogger(__name__)


class CapabilityInferenceService:
    """
    Deterministic rule-based inference engine that assigns required capabilities
    to tasks based on their goal and description.
    """

    def __init__(self, registry: Dict[str, Any] = None, decision_engine=None):
        """
        Initialize the inference service with a configurable capability registry.
        """
        self.registry = registry or CAPABILITY_REGISTRY
        from app.services.decisions.engine import DecisionEngine

        self.decision_engine = decision_engine or DecisionEngine()

    def infer(self, goal: str, description: str = "") -> CapabilityDecision:
        """
        Analyze the task goal and description and determine the required capability.

        Returns:
            CapabilityDecision containing the inferred capability, confidence,
            matched keywords, ranked scores, and reasoning.
        """
        combined_text = f"{goal} {description}".lower()

        # Tokenize text cleanly (alphanumeric words)
        re.findall(r"\b\w+\b", combined_text)

        scores: Dict[str, float] = {cap: 0.0 for cap in self.registry}
        matches: Dict[str, List[str]] = {cap: [] for cap in self.registry}

        # Score each capability
        for cap_name, cap_data in self.registry.items():
            keywords = cap_data.get("keywords", {})
            for kw, weight in keywords.items():
                # For words with special characters or spaces, simple string match might over-count,
                # but we can use regex to find whole occurrences.
                pattern = r"\b" + re.escape(kw) + r"\b"
                # If the keyword starts/ends with non-word character (like /), \b might not work exactly as expected
                # So we fallback to a simpler count for those cases
                if not kw[0].isalnum() or not kw[-1].isalnum():
                    count = combined_text.count(kw)
                else:
                    count = len(re.findall(pattern, combined_text))

                if count > 0:
                    scores[cap_name] += weight * count
                    if kw not in matches[cap_name]:
                        matches[cap_name].append(kw)

        # Rank capabilities by score
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)

        top_cap = ranked[0][0]
        top_score = ranked[0][1]

        # Determine confidence
        # A simple confidence metric: top_score / (sum(all_scores) + 1.0) or simply normalizing it to [0, 1] range via an asymptote
        # To make it simple and bounded:
        # If top_score is 0, confidence is 0.
        # If there's a huge gap between 1st and 2nd, confidence is higher.
        if top_score == 0:
            top_cap = "General"  # Fallback
            confidence = 0.0
            reasoning = "No capability keywords matched. Falling back to General."
        else:
            second_score = ranked[1][1] if len(ranked) > 1 else 0.0

            # Base confidence on raw score (maxing out around 5.0) and margin of victory
            base_confidence = min(top_score / 5.0, 0.8)
            margin = top_score - second_score
            margin_bonus = min(margin / max(top_score, 1.0) * 0.2, 0.2)

            confidence = round(base_confidence + margin_bonus, 2)
            matched_kws = matches[top_cap]
            reasoning = f"Matched keywords {matched_kws} for capability '{top_cap}' with score {top_score}."

        decision = CapabilityDecision(
            required_capability=top_cap,
            confidence=confidence,
            ranked_scores=scores,
            matched_keywords=matches,
            reasoning=reasoning,
        )

        # Emit telemetry
        logger.info(
            f"Capability Inference | Task: '{goal[:30]}...' | "
            f"Inferred: {decision.required_capability} | Confidence: {decision.confidence} | "
            f"Reasoning: {decision.reasoning}"
        )

        from app.services.decisions.models import DecisionType

        self.decision_engine.record_decision(
            decision_type=DecisionType.CAPABILITY,
            component="CapabilityInference",
            selected_option=decision.required_capability,
            context={"historical_success": 0.8, "llm_confidence": confidence},
        )

        return decision
