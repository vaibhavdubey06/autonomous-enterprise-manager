import logging
from typing import Dict, Any, List
from app.services.reflection.reflection_engine import ReflectionEngine
from app.services.decisions.models import DecisionRecord, DecisionType

logger = logging.getLogger(__name__)


class WorkflowOptimizer:
    """
    Distills reflections into actionable heuristics for:
    - Planner
    - Capability Inference
    - Retrieval Engine
    - Model Router
    """

    def __init__(self):
        self.reflection_engine = ReflectionEngine()
        self.global_heuristics: List[str] = []
        self.decision_history: List[DecisionRecord] = []

    def log_decisions(self, decisions: List[DecisionRecord]):
        self.decision_history.extend(decisions)
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]

    def optimize_from_state(self, state: dict) -> None:
        """Runs reflection and converts it into heuristics."""
        reflections = self.reflection_engine.reflect_on_workflow(state)
        
        # Analyze decision history for this run (assuming decision engine populated them)
        # Ideally we'd map decisions to the specific trace ID.
        
        heuristics = reflections.get("heuristics", [])
        
        # Derive heuristics from recent decisions
        recent_routing = [d for d in self.decision_history[-10:] if d.decision_type == DecisionType.ROUTING]
        for d in recent_routing:
            if getattr(d, 'success', False):
                heuristics.append(f"Provider {d.selected_option} performed well recently (conf {d.confidence:.2f}).")
                
        for h in heuristics:
            logger.info(f"[Optimizer] New Heuristic Learned: {h}")
            self.global_heuristics.append(h)
            
        # Limit heuristic cache
        if len(self.global_heuristics) > 100:
            self.global_heuristics = self.global_heuristics[-100:]
            
    def get_heuristics_for_planner(self) -> str:
        """Returns consolidated heuristics for the planner prompt."""
        if not self.global_heuristics:
            return ""
        return "Learned Heuristics from past runs:\n" + "\n".join(f"- {h}" for h in self.global_heuristics[-5:])
