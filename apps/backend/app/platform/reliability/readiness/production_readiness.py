from app.platform.reliability.readiness.slo_tracker import SLOTracker


class ProductionReadinessAnalyzer:
    def __init__(self, slo_tracker: SLOTracker):
        self.slo_tracker = slo_tracker

    def evaluate(self) -> dict:
        score = 100
        issues = []

        availability = self.slo_tracker.get_availability()
        budget = self.slo_tracker.get_error_budget_remaining()

        if availability < 0.999:
            score -= 20
            issues.append(f"Availability below target: {availability*100:.2f}%")

        if budget < 50.0:
            score -= 15
            issues.append(f"Error budget depleted: only {budget:.2f}% remaining")

        # In a real system, we would also check DLQ depths, Circuit Breaker states, etc.

        return {
            "readiness_score": max(0, score),
            "status": "READY" if score >= 80 else "NEEDS_IMPROVEMENT",
            "top_risks": issues,
        }
