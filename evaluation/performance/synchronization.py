import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SynchronizationEvaluator:
    """Evaluates the SLAs and performance of the Knowledge Synchronization Platform."""

    def __init__(self):
        self.sla_thresholds = {
            "max_freshness_delay_seconds": 300,  # 5 minutes
            "max_queue_delay_seconds": 60,
            "min_webhook_success_rate": 0.99,
        }

    def evaluate(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not metrics:
            return {"status": "no_data"}

        total_syncs = len(metrics)
        failed_syncs = sum(1 for m in metrics if m.get("status") == "failed")
        webhook_success_rate = (
            (total_syncs - failed_syncs) / total_syncs if total_syncs > 0 else 1.0
        )

        avg_freshness = sum(m.get("freshness_delay", 0) for m in metrics) / total_syncs
        avg_queue_delay = sum(m.get("queue_delay", 0) for m in metrics) / total_syncs

        report = {
            "total_syncs_evaluated": total_syncs,
            "webhook_success_rate": webhook_success_rate,
            "avg_freshness_delay": avg_freshness,
            "avg_queue_delay": avg_queue_delay,
            "sla_met": True,
        }

        if webhook_success_rate < self.sla_thresholds["min_webhook_success_rate"]:
            report["sla_met"] = False
            logger.warning(
                f"SLA violation: webhook success rate {webhook_success_rate} < {self.sla_thresholds['min_webhook_success_rate']}"
            )

        if avg_freshness > self.sla_thresholds["max_freshness_delay_seconds"]:
            report["sla_met"] = False
            logger.warning(
                f"SLA violation: avg freshness delay {avg_freshness} > {self.sla_thresholds['max_freshness_delay_seconds']}"
            )

        return report
