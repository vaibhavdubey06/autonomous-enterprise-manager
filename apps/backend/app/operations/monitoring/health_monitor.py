from typing import Dict, List
import datetime


class HealthStatus:
    HEALTHY = "Healthy"
    BUSY = "Busy"
    IDLE = "Idle"
    WARNING = "Warning"
    DEGRADED = "Degraded"
    RECOVERING = "Recovering"
    CRITICAL = "Critical"
    OFFLINE = "Offline"


class HealthRule:
    def __init__(
        self,
        subsystem: str,
        metric_name: str,
        warning_threshold: float,
        critical_threshold: float,
        comparison: str = "gt",
    ):
        self.subsystem = subsystem
        self.metric_name = metric_name
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.comparison = comparison  # "gt" or "lt"


class HealthMonitor:
    """Tracks subsystem health across 8 states with configurable rules."""

    def __init__(self):
        self._status: Dict[str, str] = {}
        self._rules: List[HealthRule] = []
        self._history: List[Dict] = []

    def register_subsystem(self, name: str, initial_status: str = HealthStatus.HEALTHY):
        self._status[name] = initial_status

    def add_rule(self, rule: HealthRule):
        self._rules.append(rule)

    def set_status(self, subsystem: str, status: str):
        old = self._status.get(subsystem)
        self._status[subsystem] = status
        if old != status:
            self._history.append(
                {
                    "subsystem": subsystem,
                    "from": old,
                    "to": status,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            )

    def evaluate_rule(self, rule: HealthRule, current_value: float):
        if rule.comparison == "gt":
            if current_value > rule.critical_threshold:
                self.set_status(rule.subsystem, HealthStatus.CRITICAL)
            elif current_value > rule.warning_threshold:
                self.set_status(rule.subsystem, HealthStatus.WARNING)
            else:
                self.set_status(rule.subsystem, HealthStatus.HEALTHY)
        elif rule.comparison == "lt":
            if current_value < rule.critical_threshold:
                self.set_status(rule.subsystem, HealthStatus.CRITICAL)
            elif current_value < rule.warning_threshold:
                self.set_status(rule.subsystem, HealthStatus.WARNING)
            else:
                self.set_status(rule.subsystem, HealthStatus.HEALTHY)

    def get_status(self, subsystem: str) -> str:
        return self._status.get(subsystem, HealthStatus.OFFLINE)

    def get_all_status(self) -> Dict[str, str]:
        return dict(self._status)

    def get_history(self) -> List[Dict]:
        return self._history
