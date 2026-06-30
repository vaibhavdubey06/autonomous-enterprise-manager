import psutil
from typing import Dict, Any
from app.operations.metrics.metrics_registry import MetricsRegistry


class MetricsCollector:
    """Collects system, application, and business metrics."""

    def __init__(self, registry: MetricsRegistry):
        self.registry = registry

    def collect_system_metrics(self) -> Dict[str, Any]:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        self.registry.set_gauge("system.cpu_percent", cpu)
        self.registry.set_gauge("system.ram_percent", mem.percent)
        self.registry.set_gauge("system.ram_used_mb", mem.used / (1024 * 1024))
        self.registry.set_gauge("system.disk_percent", disk.percent)
        self.registry.set_gauge("system.threads", float(psutil.cpu_count() or 0))

        return {
            "cpu_percent": cpu,
            "ram_percent": mem.percent,
            "ram_used_mb": round(mem.used / (1024 * 1024), 1),
            "disk_percent": disk.percent,
            "threads": psutil.cpu_count(),
        }

    def record_latency(self, component: str, duration_ms: float):
        self.registry.record_histogram(f"latency.{component}", duration_ms)
        self.registry.increment(f"count.{component}")

    def record_success(self, component: str):
        self.registry.increment(f"success.{component}")

    def record_failure(self, component: str):
        self.registry.increment(f"failure.{component}")

    def get_summary(self) -> Dict[str, Any]:
        return {
            "counters": self.registry.get_all_counters(),
            "gauges": self.registry.get_all_gauges(),
            "histograms": {
                name: self.registry.get_histogram_stats(name)
                for name in self.registry.get_all_histogram_names()
            },
        }
