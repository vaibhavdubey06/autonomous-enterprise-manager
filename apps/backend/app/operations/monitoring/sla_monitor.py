from typing import Dict, List, Any
from app.operations.metrics.metrics_registry import MetricsRegistry


class SLATarget:
    def __init__(
        self, name: str, metric_name: str, target_value: float, comparison: str = "gte"
    ):
        self.name = name
        self.metric_name = metric_name
        self.target_value = target_value
        self.comparison = comparison  # "gte" (greater-than-or-equal), "lte"


class SLAMonitor:
    """Monitors SLA targets and generates compliance reports."""

    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self._targets: List[SLATarget] = []

    def add_target(self, target: SLATarget):
        self._targets.append(target)

    def evaluate(self) -> List[Dict[str, Any]]:
        results = []
        for target in self._targets:
            current = self.registry.get_gauge(target.metric_name)
            if current is None:
                current = self.registry.get_counter(target.metric_name)
            met = False
            if current is not None:
                if target.comparison == "gte":
                    met = current >= target.target_value
                elif target.comparison == "lte":
                    met = current <= target.target_value
            results.append(
                {
                    "name": target.name,
                    "target": target.target_value,
                    "current": current,
                    "met": met,
                }
            )
        return results
