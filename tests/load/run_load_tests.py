import asyncio
import time


async def simulate_workflow_request(user_id: int):
    # Simulate a workflow request
    await asyncio.sleep(0.1)  # Simulate network IO
    return True


async def run_load_test(concurrent_users: int):
    print(f"Starting load test with {concurrent_users} concurrent users...")
    start_time = time.time()

    tasks = [simulate_workflow_request(i) for i in range(concurrent_users)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    duration = end_time - start_time

    successes = sum(1 for r in results if r is True)
    print(f"Completed in {duration:.2f}s")
    print(f"Throughput: {concurrent_users / duration:.2f} req/s")
    print(f"Success Rate: {successes / concurrent_users * 100:.2f}%")


if __name__ == "__main__":
    for users in [100, 500, 1000]:
        asyncio.run(run_load_test(users))
