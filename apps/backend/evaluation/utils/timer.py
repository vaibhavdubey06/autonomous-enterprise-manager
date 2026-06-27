import time
import math
import statistics
from contextlib import contextmanager

def get_percentile(data, percent):
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1

class BenchmarkTimer:
    def __init__(self):
        self.timings = {}

    @contextmanager
    def measure(self, name: str):
        start = time.time()
        yield
        end = time.time()
        elapsed_ms = (end - start) * 1000
        if name not in self.timings:
            self.timings[name] = []
        self.timings[name].append(elapsed_ms)
        
    def get_metrics(self):
        res = {}
        for k, v in self.timings.items():
            if not v: continue
            res[k] = {
                "avg_ms": statistics.mean(v),
                "median_ms": statistics.median(v),
                "stdev_ms": statistics.stdev(v) if len(v) > 1 else 0.0,
                "min_ms": min(v),
                "max_ms": max(v),
                "p50_ms": get_percentile(v, 0.50),
                "p90_ms": get_percentile(v, 0.90),
                "p95_ms": get_percentile(v, 0.95),
                "p99_ms": get_percentile(v, 0.99),
                "count": len(v)
            }
        return res
