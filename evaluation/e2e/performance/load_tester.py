import asyncio
import time
import psutil
from typing import List, Dict, Any


class LoadTester:
    """
    Executes concurrent load tests against the E2E API runner.
    Monitors system resource utilization using psutil.
    """

    def __init__(self, runner):
        self.runner = runner
        self.metrics = []
        self._monitoring = False

    async def _monitor_resources(self):
        """Background task to poll CPU/Memory usage."""
        process = psutil.Process()
        self._monitoring = True

        while self._monitoring:
            self.metrics.append(
                {
                    "time": time.time(),
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "memory_mb": process.memory_info().rss / (1024 * 1024),
                    "connections": len(process.connections()),
                }
            )
            await asyncio.sleep(1)

    async def run_load_test(
        self, scenarios: List[Dict[str, Any]], concurrency_levels: List[int]
    ):
        """
        Runs scenarios at different concurrency levels (1, 5, 10, 25, etc.).
        """
        results = {}

        # Start resource monitor
        monitor_task = asyncio.create_task(self._monitor_resources())

        try:
            for concurrency in concurrency_levels:
                print(f"--- Starting Load Test at Concurrency: {concurrency} ---")

                # We'll dispatch 'concurrency' number of scenarios concurrently
                tasks = []
                for i in range(concurrency):
                    # Wrap around scenarios if concurrency > len(scenarios)
                    scenario = scenarios[i % len(scenarios)]
                    tasks.append(self.runner._execute_single(scenario))

                start_time = time.time()
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                latency = time.time() - start_time

                results[concurrency] = {
                    "latency_sec": latency,
                    "throughput_req_per_sec": concurrency / latency
                    if latency > 0
                    else 0,
                    "success_count": sum(
                        1 for r in batch_results if getattr(r, "success", False)
                    ),
                    "error_count": sum(
                        1
                        for r in batch_results
                        if isinstance(r, Exception) or not getattr(r, "success", False)
                    ),
                }

                # Small cooldown between batches
                await asyncio.sleep(2)

        finally:
            self._monitoring = False
            await monitor_task

        return {"load_results": results, "resource_metrics": self.metrics}
