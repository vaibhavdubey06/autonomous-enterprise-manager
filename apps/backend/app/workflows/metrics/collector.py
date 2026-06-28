import time
from typing import Dict, Any, Optional

class MetricsCollector:
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "start_time": time.time(),
            "end_time": None,
            "duration_ms": 0,
            "task_metrics": {}
        }
        
    def record_task_start(self, task_id: str) -> None:
        self.metrics["task_metrics"][task_id] = {
            "start_time": time.time(),
            "end_time": None,
            "duration_ms": 0,
            "retries": 0,
            "status": "Running"
        }
        
    def record_task_end(self, task_id: str, status: str) -> None:
        if task_id in self.metrics["task_metrics"]:
            task_metric = self.metrics["task_metrics"][task_id]
            task_metric["end_time"] = time.time()
            task_metric["duration_ms"] = (task_metric["end_time"] - task_metric["start_time"]) * 1000
            task_metric["status"] = status
            
    def record_task_retry(self, task_id: str) -> None:
        if task_id in self.metrics["task_metrics"]:
            self.metrics["task_metrics"][task_id]["retries"] += 1
            
    def complete_workflow(self) -> Dict[str, Any]:
        self.metrics["end_time"] = time.time()
        self.metrics["duration_ms"] = (self.metrics["end_time"] - self.metrics["start_time"]) * 1000
        return self.metrics
