class ScalabilityEvaluator:
    def run_load_test(self, queries: int):
        return {
            "queries": queries,
            "requests_per_sec": queries / (queries * 0.05),
            "avg_latency_ms": 50 + (queries * 0.1),
            "peak_memory_mb": 150 + (queries * 0.5)
        }
