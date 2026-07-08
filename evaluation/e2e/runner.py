import os
import sys
import uuid
import time
import json
import asyncio
from typing import Dict, Any

os.environ["USE_SQLITE"] = "true"

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend")))

from fastapi.testclient import TestClient
from app.main import app
from app.operations.tracing.trace_manager import TraceManager
from app.operations.tracing.exporter import InMemoryTraceExporter
from evaluation.e2e.failure_matrix import FailureInjector
from evaluation.e2e.factory.scenario_factory import ScenarioFactory
from evaluation.metrics.aggregator import MetricsAggregator
from evaluation.models import EvaluationResult, ExecutionStatus, FailureCategory

class E2ERunner:
    def __init__(self, mode: str = "local", base_url: str = "http://localhost:8000"):
        self.mode = mode
        self.base_url = base_url
        self.exporter = InMemoryTraceExporter()
        TraceManager.register_exporter(self.exporter)
        
        # TestClient for local execution bypassing network stack
        self.client = TestClient(app) if mode == "local" else None
        
    async def _execute_single(self, scenario: Dict[str, Any]) -> EvaluationResult:
        self.exporter.clear()
        q_id = scenario["id"]
        query = scenario["user_input"]
        session_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        
        start_time = time.time()
        
        payload = {
            "session_id": session_id,
            "conversation_id": conversation_id,
            "question": query
        }
        
        response_text = ""
        error_msg = ""
        exec_status = ExecutionStatus.FAILED
        fail_cat = FailureCategory.NONE
        fail_rsn = None
        
        with FailureInjector.inject(scenario):
            try:
                if self.mode == "local":
                    response = self.client.post("/api/v1/agent/chat", json=payload)
                    if response.status_code == 200:
                        response_text = response.json().get("answer", "")
                        exec_status = ExecutionStatus.SUCCESS if response_text else ExecutionStatus.FAILED
                    else:
                        error_msg = response.text
                else:
                    # For CI/Production, use standard HTTPX (synchronous wait for demo)
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.post(f"{self.base_url}/api/v1/agent/chat", json=payload, timeout=60.0)
                        if response.status_code == 200:
                            response_text = response.json().get("answer", "")
                            exec_status = ExecutionStatus.SUCCESS if response_text else ExecutionStatus.FAILED
                        else:
                            error_msg = response.text
            except Exception as e:
                error_msg = str(e)
                fail_cat = FailureCategory.INFRASTRUCTURE
                fail_rsn = str(e)
                if "quota" in error_msg.lower() or "timeout" in error_msg.lower():
                    fail_cat = FailureCategory.PROVIDER
                elif "unreachable" in error_msg.lower() or "unavailable" in error_msg.lower():
                    fail_cat = FailureCategory.INFRASTRUCTURE
                    
        latency = (time.time() - start_time) * 1000
        
        traces_list = []
        for trace_id, spans in self.exporter.get_all_traces().items():
            traces_list.extend(spans)
            
        return EvaluationResult(
            scenario_id=q_id,
            query=query,
            ground_truth="",
            expected_capability=",".join(scenario.get("expected_capabilities", [])),
            expected_agent=",".join(scenario.get("expected_agents", [])),
            expected_provider=scenario.get("expected_provider", "unknown"),
            expected_tools=scenario.get("expected_tools", []),
            expected_guardrails=scenario.get("expected_guardrails", []),
            success=bool(response_text),
            execution_status=exec_status,
            failure_category=fail_cat,
            failure_reason=fail_rsn,
            actual_answer=response_text,
            error=error_msg,
            latency_ms=latency,
            traces=traces_list
        )
        
    async def run_all(self, scenarios: list) -> Dict[str, EvaluationResult]:
        results = {}
        for scenario in scenarios:
            print(f"Executing [E2E - {self.mode}] {scenario['id']}: {scenario['user_input']}")
            results[scenario['id']] = await self._execute_single(scenario)
        return results

if __name__ == "__main__":
    # Generate scenarios
    datasets_dir = os.path.join(os.path.dirname(__file__), "datasets")
    factory = ScenarioFactory(datasets_dir)
    scenarios_path = factory.generate()
    
    with open(scenarios_path, "r") as f:
        scenarios = json.load(f)
        
    # Limit for basic execution (full run takes long)
    scenarios = scenarios[:10] 
    
    runner = E2ERunner(mode="local")
    results = asyncio.run(runner.run_all(scenarios))
    
    metrics = MetricsAggregator(results).evaluate()
    print("E2E Execution Complete. Evaluated", len(results), "scenarios.")
