from typing import List, Dict, Any
from app.operations.alerts.alert_rules import AlertRule, Alert
from app.operations.metrics.metrics_registry import MetricsRegistry


class AlertManager:
    """Evaluates rules against live metrics and fires alerts. Transport-agnostic."""

    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self._rules: List[AlertRule] = []
        self._alerts: List[Alert] = []
        self._handlers: List = []  # Future: Slack, PagerDuty, Email handlers

    def add_rule(self, rule: AlertRule):
        self._rules.append(rule)

    def add_handler(self, handler):
        self._handlers.append(handler)

    def evaluate_all(self) -> List[Alert]:
        fired = []
        for rule in self._rules:
            current = self.registry.get_gauge(rule.metric_name)
            if current is None:
                stats = self.registry.get_histogram_stats(rule.metric_name)
                current = stats.get("average") if stats else None
            if current is None:
                current = self.registry.get_counter(rule.metric_name)
            if current is None:
                continue

            triggered = False
            if rule.condition == "gt" and current > rule.threshold:
                triggered = True
            elif rule.condition == "lt" and current < rule.threshold:
                triggered = True
            elif rule.condition == "eq" and current == rule.threshold:
                triggered = True

            if triggered:
                alert = Alert(
                    rule_id=rule.rule_id,
                    metric_name=rule.metric_name,
                    current_value=current,
                    threshold=rule.threshold,
                    severity=rule.severity,
                    message=f"{rule.metric_name} is {current} (threshold: {rule.condition} {rule.threshold})",
                )
                self._alerts.append(alert)
                fired.append(alert)
                for handler in self._handlers:
                    try:
                        handler(alert)
                    except Exception:
                        pass
        return fired

    def get_alerts(self) -> List[Dict[str, Any]]:
        return [a.model_dump(mode="json") for a in self._alerts]
