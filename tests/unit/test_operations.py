import time
from app.operations.telemetry.telemetry_models import TelemetryEvent
from app.operations.telemetry.telemetry_context import TelemetryContext
from app.operations.telemetry.telemetry_pipeline import TelemetryPipeline
from app.operations.telemetry.telemetry_manager import TelemetryManager
from app.operations.tracing.trace_manager import TraceManager
from app.operations.tracing.correlation_engine import CorrelationEngine
from app.operations.logging.structured_logger import StructuredLogger, LogRepository
from app.operations.exporters.console_exporter import JsonExporter, OTelExporter
from app.operations.metrics.metrics_registry import MetricsRegistry
from app.operations.metrics.metrics_collector import MetricsCollector
from app.operations.cost.token_tracker import TokenTracker
from app.operations.cost.cost_tracker import CostTracker
from app.operations.profiling.latency_profiler import (
    LatencyProfiler,
    WorkflowProfiler,
    BaselineManager,
)
from app.operations.monitoring.health_monitor import (
    HealthMonitor,
    HealthStatus,
    HealthRule,
)
from app.operations.monitoring.sla_monitor import SLAMonitor, SLATarget
from app.operations.alerts.alert_rules import AlertRule
from app.operations.alerts.alert_manager import AlertManager
from app.operations.analytics.analytics_engine import AnalyticsEngine
from app.operations.services.operations_service import OperationsService

# ===== TELEMETRY PIPELINE =====


class TestTelemetryPipeline:
    def test_event_creation(self):
        event = TelemetryEvent(source="Supervisor", event_type="workflow_started")
        assert event.source == "Supervisor"
        assert event.event_id != ""

    def test_pipeline_enrichment(self):
        TelemetryContext.new_context(trace_id="trace_123", correlation_id="corr_456")
        pipeline = TelemetryPipeline()
        event = TelemetryEvent(source="Workflow", event_type="task_started")
        processed = pipeline.process(event)
        assert processed.trace_id == "trace_123"
        assert processed.correlation_id == "corr_456"
        TelemetryContext.reset()

    def test_pipeline_filtering(self):
        pipeline = TelemetryPipeline()
        pipeline.add_filter(lambda e: e.source != "debug")
        kept = pipeline.process(TelemetryEvent(source="Workflow", event_type="x"))
        dropped = pipeline.process(TelemetryEvent(source="debug", event_type="x"))
        assert kept is not None
        assert dropped is None

    def test_telemetry_manager(self):
        manager = TelemetryManager()
        manager.emit("Supervisor", "goal_understood", duration_ms=5.0)
        manager.emit("Workflow", "task_completed", duration_ms=12.0)
        events = manager.get_events(source="Supervisor")
        assert len(events) == 1
        assert events[0].event_type == "goal_understood"


# ===== CORRELATION ENGINE =====


class TestCorrelationEngine:
    def test_start_and_extend(self):
        engine = CorrelationEngine()
        cid = engine.start_correlation("user")
        engine.extend_correlation(cid, "Supervisor")
        engine.extend_correlation(cid, "CTO")
        engine.extend_correlation(cid, "Workflow")
        chain = engine.get_chain(cid)
        assert chain == ["user", "Supervisor", "CTO", "Workflow"]

    def test_missing_correlation(self):
        engine = CorrelationEngine()
        assert engine.get_chain("nonexistent") == []


# ===== TRACE MANAGER =====


class TestTraceManager:
    def test_trace_creation(self):
        tm = TraceManager()
        with tm.trace("supervisor.run") as root:
            trace_id = root.trace_id
            with tm.span(trace_id, "planning", root.span_id):
                pass
        spans = tm.get_trace(trace_id)
        assert len(spans) == 2
        assert spans[0].status == "OK"
        assert spans[1].parent_span_id == root.span_id

    def test_span_duration(self):
        tm = TraceManager()
        with tm.trace("test_op") as root:
            time.sleep(0.01)
        assert root.duration_ms > 0


# ===== STRUCTURED LOGGER =====


class TestStructuredLogger:
    def test_log_and_search(self):
        logger = StructuredLogger()
        logger.info("Workflow", "Task completed")
        logger.error("Governance", "Policy violation")
        repo = LogRepository(logger)
        errors = repo.search(severity="ERROR")
        assert len(errors) == 1
        assert errors[0]["component"] == "Governance"


# ===== EXPORTER FRAMEWORK =====


class TestExporters:
    def test_json_exporter(self):
        exporter = JsonExporter()
        events = [TelemetryEvent(source="test", event_type="x")]
        exporter.export(events)
        assert len(exporter.exported) == 1

    def test_otel_exporter_no_crash(self):
        exporter = OTelExporter()
        events = [TelemetryEvent(source="test", event_type="x")]
        exporter.export(events)  # Should not crash even without OTel configured


# ===== METRICS =====


class TestMetrics:
    def test_registry_counters(self):
        reg = MetricsRegistry()
        reg.increment("requests", 1)
        reg.increment("requests", 1)
        assert reg.get_counter("requests") == 2

    def test_registry_histograms(self):
        reg = MetricsRegistry()
        for v in [10, 20, 30, 40, 50]:
            reg.record_histogram("latency", v)
        stats = reg.get_histogram_stats("latency")
        assert stats["count"] == 5
        assert stats["average"] == 30.0
        assert stats["max"] == 50

    def test_metrics_collector_system(self):
        reg = MetricsRegistry()
        collector = MetricsCollector(reg)
        sys_metrics = collector.collect_system_metrics()
        assert "cpu_percent" in sys_metrics
        assert "ram_percent" in sys_metrics


# ===== COST TRACKING =====


class TestCostTracking:
    def test_token_tracking(self):
        tracker = TokenTracker()
        tracker.record("gemini-2.5-flash", 100, 50, agent="CTO")
        tracker.record("gemini-2.5-flash", 200, 100, agent="CFO")
        assert tracker.get_total_tokens() == 450
        by_agent = tracker.get_by_agent()
        assert by_agent["CTO"] == 150
        assert by_agent["CFO"] == 300

    def test_token_estimation(self):
        tracker = TokenTracker()
        assert tracker.estimate_tokens("Hello World!") == 3  # 12 chars / 4

    def test_cost_calculation(self):
        tracker = TokenTracker()
        tracker.record("gemini-2.5-flash", 1000, 500, agent="CTO", workflow_id="wf1")
        cost = CostTracker(tracker)
        total = cost.estimate_total_cost()
        assert total > 0
        summary = cost.get_cost_summary()
        assert summary["total_tokens"] == 1500


# ===== PROFILING & BASELINES =====


class TestProfiling:
    def test_latency_profiler(self):
        reg = MetricsRegistry()
        profiler = LatencyProfiler(reg)
        for v in [5, 10, 15, 20, 100]:
            profiler.record("LLM", v)
        profile = profiler.get_profile("LLM")
        assert profile["count"] == 5
        assert profile["max"] == 100

    def test_workflow_profiler(self):
        wp = WorkflowProfiler()
        wp.record_phase("wf1", "governance", 15.0)
        wp.record_phase("wf1", "execution", 45.0)
        profile = wp.get_profile("wf1")
        assert profile["governance"] == 15.0
        assert profile["execution"] == 45.0

    def test_baseline_regression(self):
        bm = BaselineManager()
        bm.set_baseline("llm_latency", average=50.0, p95=100.0, maximum=200.0)
        ok = bm.check_regression("llm_latency", 80.0)
        assert ok["regressed"] is False
        bad = bm.check_regression("llm_latency", 150.0)
        assert bad["regressed"] is True


# ===== HEALTH MONITOR =====


class TestHealthMonitor:
    def test_default_status(self):
        hm = HealthMonitor()
        hm.register_subsystem("API")
        assert hm.get_status("API") == HealthStatus.HEALTHY

    def test_rule_evaluation(self):
        hm = HealthMonitor()
        hm.register_subsystem("LLM")
        rule = HealthRule(
            "LLM", "llm_latency", warning_threshold=500, critical_threshold=1000
        )
        hm.evaluate_rule(rule, 200)
        assert hm.get_status("LLM") == HealthStatus.HEALTHY
        hm.evaluate_rule(rule, 700)
        assert hm.get_status("LLM") == HealthStatus.WARNING
        hm.evaluate_rule(rule, 1500)
        assert hm.get_status("LLM") == HealthStatus.CRITICAL


# ===== SLA MONITOR =====


class TestSLAMonitor:
    def test_sla_evaluation(self):
        reg = MetricsRegistry()
        reg.set_gauge("api.availability", 99.9)
        sla = SLAMonitor(reg)
        sla.add_target(SLATarget("API Availability", "api.availability", 99.5, "gte"))
        results = sla.evaluate()
        assert len(results) == 1
        assert results[0]["met"] is True


# ===== ALERT MANAGER =====


class TestAlertManager:
    def test_alert_fires(self):
        reg = MetricsRegistry()
        reg.set_gauge("system.cpu_percent", 95.0)
        am = AlertManager(reg)
        am.add_rule(
            AlertRule(
                metric_name="system.cpu_percent",
                condition="gt",
                threshold=90.0,
                severity="CRITICAL",
            )
        )
        fired = am.evaluate_all()
        assert len(fired) == 1
        assert fired[0].severity == "CRITICAL"

    def test_no_alert_below_threshold(self):
        reg = MetricsRegistry()
        reg.set_gauge("system.cpu_percent", 50.0)
        am = AlertManager(reg)
        am.add_rule(
            AlertRule(metric_name="system.cpu_percent", condition="gt", threshold=90.0)
        )
        fired = am.evaluate_all()
        assert len(fired) == 0


# ===== ANALYTICS ENGINE =====


class TestAnalyticsEngine:
    def test_workflow_success_rate(self):
        reg = MetricsRegistry()
        reg.increment("success.workflow", 9)
        reg.increment("failure.workflow", 1)
        analytics = AnalyticsEngine(reg)
        rate = analytics.workflow_success_rate()
        assert rate == 90.0


# ===== OPERATIONS SERVICE =====


class TestOperationsService:
    def test_service_initialization(self):
        svc = OperationsService()
        health = svc.get_health()
        assert "Supervisor" in health
        assert "Workflow" in health
        assert health["Supervisor"] == "Healthy"

    def test_service_system_metrics(self):
        svc = OperationsService()
        sys = svc.get_system()
        assert "cpu_percent" in sys


# ===== SCENARIO TESTS =====


class TestScenarios:
    def test_scenario_1_full_workflow_trace(self):
        """Complete enterprise workflow produces correlated trace, logs, metrics, cost, analytics."""
        svc = OperationsService()

        # Start correlation
        cid = svc.correlation.start_correlation("user")
        svc.correlation.extend_correlation(cid, "Supervisor")
        svc.correlation.extend_correlation(cid, "CTO")
        svc.correlation.extend_correlation(cid, "Workflow")
        svc.correlation.extend_correlation(cid, "Governance")
        svc.correlation.extend_correlation(cid, "Capability")

        # Create trace
        with svc.trace_manager.trace("supervisor.run") as root:
            with svc.trace_manager.span(root.trace_id, "planning", root.span_id):
                svc.telemetry.emit("Supervisor", "planning_complete", duration_ms=10)
            with svc.trace_manager.span(root.trace_id, "execution", root.span_id):
                svc.telemetry.emit("Workflow", "task_executed", duration_ms=25)

        # Log
        svc.structured_logger.info("Workflow", "Task completed")

        # Token usage
        svc.token_tracker.record(
            "gemini-2.5-flash", 500, 200, agent="CTO", workflow_id="wf1"
        )

        # Metrics
        svc.metrics_collector.record_latency("workflow", 35.0)
        svc.metrics_collector.record_success("workflow")

        # Verify chain
        chain = svc.correlation.get_chain(cid)
        assert len(chain) == 6
        assert "Governance" in chain

        # Verify traces
        traces = svc.get_traces()
        assert len(traces) > 0

        # Verify cost
        cost = svc.get_cost()
        assert cost["total_tokens"] == 700

        # Verify analytics
        analytics = svc.get_analytics()
        assert analytics["workflow_success_rate"] == 100.0

    def test_scenario_2_high_latency_alert(self):
        """High-latency capability triggers an alert and health degradation."""
        svc = OperationsService()
        svc.registry.set_gauge("latency.capability", 5000.0)
        svc.alert_manager.add_rule(
            AlertRule(
                metric_name="latency.capability",
                condition="gt",
                threshold=2000.0,
                severity="CRITICAL",
            )
        )
        fired = svc.alert_manager.evaluate_all()
        assert len(fired) == 1
        assert fired[0].severity == "CRITICAL"

        # Health should degrade
        rule = HealthRule(
            "Capability",
            "latency.capability",
            warning_threshold=1000,
            critical_threshold=3000,
        )
        svc.health_monitor.evaluate_rule(rule, 5000.0)
        assert svc.health_monitor.get_status("Capability") == "Critical"

    def test_scenario_3_collaboration_telemetry(self):
        """Multiple agent collaboration produces correlated telemetry and profiles."""
        svc = OperationsService()
        cid = svc.correlation.start_correlation("user")
        svc.correlation.extend_correlation(cid, "CEO")
        svc.correlation.extend_correlation(cid, "CTO")
        svc.correlation.extend_correlation(cid, "CFO")

        svc.registry.increment("count.agent.CEO")
        svc.registry.increment("count.agent.CTO")
        svc.registry.increment("count.agent.CFO")

        agents = svc.analytics.most_active_agents()
        assert len(agents) == 3

    def test_scenario_4_baseline_regression(self):
        """Benchmark establishes baseline, regression is detected."""
        svc = OperationsService()
        svc.baseline_manager.set_baseline(
            "llm_latency", average=50.0, p95=100.0, maximum=200.0
        )

        ok = svc.baseline_manager.check_regression("llm_latency", 80.0)
        assert ok["regressed"] is False

        bad = svc.baseline_manager.check_regression("llm_latency", 150.0)
        assert bad["regressed"] is True
