from typing import Dict, Any, List
from app.operations.telemetry.telemetry_manager import TelemetryManager
from app.operations.telemetry.telemetry_pipeline import TelemetryPipeline
from app.operations.tracing.trace_manager import TraceManager
from app.operations.tracing.correlation_engine import CorrelationEngine
from app.operations.logging.structured_logger import StructuredLogger, LogRepository
from app.operations.metrics.metrics_registry import MetricsRegistry
from app.operations.metrics.metrics_collector import MetricsCollector
from app.operations.cost.token_tracker import TokenTracker
from app.operations.cost.cost_tracker import CostTracker
from app.operations.profiling.latency_profiler import LatencyProfiler, BaselineManager
from app.operations.monitoring.health_monitor import HealthMonitor
from app.operations.monitoring.sla_monitor import SLAMonitor
from app.operations.alerts.alert_manager import AlertManager
from app.operations.analytics.analytics_engine import AnalyticsEngine


class OperationsService:
    """Facade aggregating all Enterprise Operations Platform subsystems."""

    def __init__(self):
        self.pipeline = TelemetryPipeline()
        self.telemetry = TelemetryManager(self.pipeline)
        self.trace_manager = TraceManager()
        self.correlation = CorrelationEngine()
        self.structured_logger = StructuredLogger()
        self.log_repository = LogRepository(self.structured_logger)
        self.registry = MetricsRegistry()
        self.metrics_collector = MetricsCollector(self.registry)
        self.token_tracker = TokenTracker()
        self.cost_tracker = CostTracker(self.token_tracker)
        self.latency_profiler = LatencyProfiler(self.registry)
        self.baseline_manager = BaselineManager()
        self.health_monitor = HealthMonitor()
        self.sla_monitor = SLAMonitor(self.registry)
        self.alert_manager = AlertManager(self.registry)
        self.analytics = AnalyticsEngine(self.registry, self.cost_tracker)

        # Register default subsystems for health monitoring
        for sub in [
            "Supervisor",
            "Workflow",
            "Governance",
            "Collaboration",
            "Capability",
            "Memory",
            "Knowledge",
            "LLM",
            "API",
        ]:
            self.health_monitor.register_subsystem(sub)

    def get_health(self) -> Dict[str, str]:
        return self.health_monitor.get_all_status()

    def get_traces(self) -> Dict[str, List[dict]]:
        return self.trace_manager.get_all_traces()

    def get_logs(self, **kwargs) -> List[Dict[str, Any]]:
        return self.log_repository.search(**kwargs)

    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics_collector.get_summary()

    def get_cost(self) -> Dict[str, Any]:
        return self.cost_tracker.get_cost_summary()

    def get_alerts(self) -> List[Dict[str, Any]]:
        return self.alert_manager.get_alerts()

    def get_analytics(self) -> Dict[str, Any]:
        return self.analytics.generate_report()

    def get_system(self) -> Dict[str, Any]:
        return self.metrics_collector.collect_system_metrics()

    def get_baselines(self) -> Dict:
        return self.baseline_manager.get_all_baselines()

    def get_profiles(self) -> Dict:
        return self.latency_profiler.get_all_profiles()
