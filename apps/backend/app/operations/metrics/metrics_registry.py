import threading
from typing import Dict, List, Optional
from collections import defaultdict
import statistics


class MetricsRegistry:
    """Thread-safe registry of named counters, gauges, and histograms."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)

    def increment(self, name: str, value: float = 1.0):
        with self._lock:
            self._counters[name] += value

    def set_gauge(self, name: str, value: float):
        with self._lock:
            self._gauges[name] = value

    def record_histogram(self, name: str, value: float):
        with self._lock:
            self._histograms[name].append(value)

    def get_counter(self, name: str) -> float:
        return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> Optional[float]:
        return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        values = self._histograms.get(name, [])
        if not values:
            return {}
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        return {
            "count": n,
            "average": statistics.mean(sorted_vals),
            "median": statistics.median(sorted_vals),
            "p50": sorted_vals[int(n * 0.5)] if n > 0 else 0,
            "p90": sorted_vals[int(n * 0.9)] if n > 1 else sorted_vals[-1],
            "p95": sorted_vals[int(n * 0.95)] if n > 1 else sorted_vals[-1],
            "p99": sorted_vals[int(n * 0.99)] if n > 1 else sorted_vals[-1],
            "max": sorted_vals[-1],
            "min": sorted_vals[0],
        }

    def get_all_counters(self) -> Dict[str, float]:
        return dict(self._counters)

    def get_all_gauges(self) -> Dict[str, float]:
        return dict(self._gauges)

    def get_all_histogram_names(self) -> List[str]:
        return list(self._histograms.keys())
