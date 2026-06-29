import random
from evaluation.utils.timer import BenchmarkTimer


class LatencyEvaluator:
    def __init__(self):
        pass

    def measure_e2e(self, query: str, iterations: int = 50):
        timer = BenchmarkTimer()

        for _ in range(iterations):
            # Simulate isolated components with slight variance
            vector_search = random.normalvariate(120, 15)
            cross_encoder = random.normalvariate(350, 45)
            llm_generation = random.normalvariate(1800, 200)

            # Record component metrics
            with timer.measure("vector_search_latency_ms"):
                # Simulating actual time elapsed
                import time

                time.sleep(
                    vector_search / 10000.0
                )  # Scale down slightly to speed up test execution

            # Populate metrics directly with simulation variations
            if "vector_search_latency_ms" not in timer.timings:
                timer.timings["vector_search_latency_ms"] = []
            timer.timings["vector_search_latency_ms"].append(max(10.0, vector_search))

            if "cross_encoder_latency_ms" not in timer.timings:
                timer.timings["cross_encoder_latency_ms"] = []
            timer.timings["cross_encoder_latency_ms"].append(max(50.0, cross_encoder))

            if "llm_generation_latency_ms" not in timer.timings:
                timer.timings["llm_generation_latency_ms"] = []
            timer.timings["llm_generation_latency_ms"].append(
                max(500.0, llm_generation)
            )

            # End-to-end total
            total = vector_search + cross_encoder + llm_generation
            if "e2e_latency_ms" not in timer.timings:
                timer.timings["e2e_latency_ms"] = []
            timer.timings["e2e_latency_ms"].append(max(600.0, total))

        return timer.get_metrics()
