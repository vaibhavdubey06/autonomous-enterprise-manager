import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def make_health_request():
    start = time.time()
    res = client.get("/health")
    latency = time.time() - start
    return res.status_code, latency


@pytest.mark.asyncio
async def test_concurrent_workload_performance():
    """
    Simulates a production burst workload of 50 concurrent requests.
    Validates that:
    1. No requests are dropped or return 500.
    2. The 95th percentile latency is within acceptable limits (< 500ms for health check).
    """
    concurrent_requests = 50

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=20) as pool:
        tasks = [
            loop.run_in_executor(pool, make_health_request)
            for _ in range(concurrent_requests)
        ]
        results = await asyncio.gather(*tasks)

    status_codes = [r[0] for r in results]
    latencies = [r[1] for r in results]

    # All requests must succeed
    assert all(
        code == 200 for code in status_codes
    ), "Some requests failed during concurrent load"

    # Check latencies
    latencies.sort()
    p95_latency = latencies[int(len(latencies) * 0.95)]

    # Health checks should be very fast, even under load
    assert p95_latency < 0.5, f"p95 Latency too high: {p95_latency}s"
