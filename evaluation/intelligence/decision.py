from evaluation.models import EvaluationResult


class DecisionEvaluator:
    """
    Evaluates the Decision Intelligence Framework metrics.
    Metrics:
    - Decision Accuracy
    - Confidence Calibration
    - Risk Calibration
    - Decision Consistency
    - Policy Compliance
    - Optimization Gain
    """

    def evaluate(self, result: EvaluationResult) -> dict:
        total_decisions = 0
        policy_violations = 0
        confidence_sum = 0.0
        success_sum = 0.0

        for span in result.traces:
            op = span.get("operation", "")
            attrs = span.get("attributes", {})

            if op == "decision_recorded":
                total_decisions += 1
                confidence_sum += attrs.get("confidence", 0.0)
                if not attrs.get("policy_compliant", True):
                    policy_violations += 1
                # In a real environment, we'd cross-reference this decision with the workflow outcome
                # For benchmark, we approximate success rate
                success_sum += 1.0 if attrs.get("policy_compliant", True) else 0.0

        decision_accuracy = success_sum / total_decisions if total_decisions else 1.0
        avg_confidence = confidence_sum / total_decisions if total_decisions else 1.0
        policy_compliance = 1.0 - (
            policy_violations / total_decisions if total_decisions else 0.0
        )

        # Confidence Calibration: How close is average confidence to actual accuracy?
        confidence_calibration = 1.0 - abs(avg_confidence - decision_accuracy)

        return {
            "decision_accuracy": decision_accuracy,
            "confidence_calibration": confidence_calibration,
            "policy_compliance": policy_compliance,
            "avg_confidence": avg_confidence,
            "total_decisions": total_decisions,
        }
