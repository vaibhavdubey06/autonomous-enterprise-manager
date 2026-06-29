from typing import Dict
from app.operations.metrics.metrics_registry import MetricsRegistry


class LatencyProfiler:
    """Records latency samples per subsystem. Calculates P50/P90/P95/P99/Max/Average."""

    def __init__(self, registry: MetricsRegistry):
        self.registry = registry

    def record(self, subsystem: str, duration_ms: float):
        self.registry.record_histogram(f"profile.{subsystem}", duration_ms)

    def get_profile(self, subsystem: str) -> Dict[str, float]:
        return self.registry.get_histogram_stats(f"profile.{subsystem}")

    def get_all_profiles(self) -> Dict[str, Dict[str, float]]:
        names = self.registry.get_all_histogram_names()
        return {
            n.replace("profile.", ""): self.registry.get_histogram_stats(n)
            for n in names
            if n.startswith("profile.")
        }


class WorkflowProfiler:
    """Profiles end-to-end workflow execution, breaking down time per phase."""

    def __init__(self):
        self._profiles: Dict[str, Dict[str, float]] = {}

    def record_phase(self, workflow_id: str, phase: str, duration_ms: float):
        if workflow_id not in self._profiles:
            self._profiles[workflow_id] = {}
        self._profiles[workflow_id][phase] = duration_ms

    def get_profile(self, workflow_id: str) -> Dict[str, float]:
        return self._profiles.get(workflow_id, {})

    def get_all_profiles(self) -> Dict[str, Dict[str, float]]:
        return self._profiles


class BaselineManager:
    """Stores performance baselines for regression detection."""

    def __init__(self):
        self._baselines: Dict[str, Dict[str, float]] = {}

    def set_baseline(
        self, metric_name: str, average: float, p95: float, maximum: float
    ):
        self._baselines[metric_name] = {
            "average": average,
            "p95": p95,
            "maximum": maximum,
        }

    def check_regression(self, metric_name: str, current_value: float) -> Dict:
        baseline = self._baselines.get(metric_name)
        if not baseline:
            return {"regressed": False, "reason": "No baseline set"}
        if current_value > baseline["p95"]:
            return {
                "regressed": True,
                "reason": f"Current {current_value:.1f}ms exceeds P95 baseline {baseline['p95']:.1f}ms",
                "baseline": baseline,
                "current": current_value,
            }
        return {"regressed": False, "current": current_value, "baseline": baseline}

    def get_all_baselines(self) -> Dict[str, Dict[str, float]]:
        return self._baselines
