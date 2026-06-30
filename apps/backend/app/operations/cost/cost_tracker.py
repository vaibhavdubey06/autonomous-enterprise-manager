from typing import Dict, Any, Optional
from collections import defaultdict
from app.operations.cost.token_tracker import TokenTracker

# Configurable per-model pricing (USD per 1M tokens)
DEFAULT_PRICING = {
    "gemini-2.0-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "default": {"input": 0.10, "output": 0.40},
}


class CostTracker:
    """Estimates cost from token counts using configurable per-model pricing."""

    def __init__(
        self, token_tracker: TokenTracker, pricing: Optional[Dict[str, Any]] = None
    ):
        self.token_tracker = token_tracker
        self.pricing = pricing or DEFAULT_PRICING

    def _get_pricing(self, model: str) -> Dict[str, float]:
        return self.pricing.get(model, self.pricing["default"])

    def estimate_total_cost(self) -> float:
        total = 0.0
        for rec in self.token_tracker.records:
            pricing = self._get_pricing(rec.model)
            total += rec.input_tokens * pricing["input"] / 1_000_000
            total += rec.output_tokens * pricing["output"] / 1_000_000
        return round(total, 6)

    def cost_by_agent(self) -> Dict[str, float]:
        by_agent: Dict[str, float] = defaultdict(float)
        for rec in self.token_tracker.records:
            pricing = self._get_pricing(rec.model)
            cost = (rec.input_tokens * pricing["input"] / 1_000_000) + (
                rec.output_tokens * pricing["output"] / 1_000_000
            )
            by_agent[rec.agent] += cost
        return {k: round(v, 6) for k, v in by_agent.items()}

    def cost_by_workflow(self) -> Dict[str, float]:
        by_wf: Dict[str, float] = defaultdict(float)
        for rec in self.token_tracker.records:
            pricing = self._get_pricing(rec.model)
            cost = (rec.input_tokens * pricing["input"] / 1_000_000) + (
                rec.output_tokens * pricing["output"] / 1_000_000
            )
            by_wf[rec.workflow_id] += cost
        return {k: round(v, 6) for k, v in by_wf.items()}

    def get_cost_summary(self) -> Dict[str, Any]:
        return {
            "total_cost_usd": self.estimate_total_cost(),
            "total_tokens": self.token_tracker.get_total_tokens(),
            "records_count": len(self.token_tracker.records),
            "by_agent": self.cost_by_agent(),
            "by_workflow": self.cost_by_workflow(),
        }
