from pydantic import BaseModel
from typing import Dict
import time


class CollaborationMetrics(BaseModel):
    session_id: str
    delegation_accuracy: float = 1.0
    average_delegation_time_ms: float = 0.0
    negotiation_success_rate: float = 1.0
    consensus_accuracy: float = 1.0
    conflict_resolution_rate: float = 1.0
    messages_exchanged: int = 0
    decision_count: int = 0
    agent_utilization: Dict[str, float] = {}
    collaboration_success_rate: float = 1.0
    team_efficiency: float = 1.0
    start_time: float = 0.0
    end_time: float = 0.0

    def start(self):
        self.start_time = time.time()

    def end(self):
        self.end_time = time.time()
