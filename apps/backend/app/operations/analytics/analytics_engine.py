from typing import Dict, Any, List, Optional
from app.operations.metrics.metrics_registry import MetricsRegistry
from app.operations.cost.cost_tracker import CostTracker


class AnalyticsEngine:
    """Generates operational analytics from collected metrics and cost data."""

    def __init__(
        self, registry: MetricsRegistry, cost_tracker: Optional[CostTracker] = None
    ):
        self.registry = registry
        self.cost_tracker = cost_tracker

    def top_workflows(self, limit: int = 10) -> List[Dict[str, Any]]:
        counters = self.registry.get_all_counters()
        wf_counts = {
            k.replace("count.", ""): v
            for k, v in counters.items()
            if k.startswith("count.workflow.")
        }
        sorted_wf = sorted(wf_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"workflow": k, "executions": v} for k, v in sorted_wf[:limit]]

    def most_active_agents(self, limit: int = 10) -> List[Dict[str, Any]]:
        counters = self.registry.get_all_counters()
        agent_counts = {
            k.replace("count.agent.", ""): v
            for k, v in counters.items()
            if k.startswith("count.agent.")
        }
        sorted_agents = sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"agent": k, "executions": v} for k, v in sorted_agents[:limit]]

    def highest_cost_capabilities(self) -> List[Dict[str, Any]]:
        if not self.cost_tracker:
            return []
        by_wf = self.cost_tracker.cost_by_workflow()
        sorted_caps = sorted(by_wf.items(), key=lambda x: x[1], reverse=True)
        return [{"capability": k, "cost_usd": v} for k, v in sorted_caps[:10]]

    def workflow_success_rate(self) -> float:
        success = self.registry.get_counter("success.workflow")
        failure = self.registry.get_counter("failure.workflow")
        total = success + failure
        return round((success / total) * 100, 1) if total > 0 else 100.0

    def generate_report(self) -> Dict[str, Any]:
        return {
            "top_workflows": self.top_workflows(),
            "most_active_agents": self.most_active_agents(),
            "highest_cost_capabilities": self.highest_cost_capabilities(),
            "workflow_success_rate": self.workflow_success_rate(),
            "cost_summary": (
                self.cost_tracker.get_cost_summary() if self.cost_tracker else {}
            ),
        }
