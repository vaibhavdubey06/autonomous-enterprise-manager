from typing import List, Dict, Any, Optional
from app.agents.supervisor.schemas import ExecutionPlan
from app.collaboration.schemas.executive import DecisionStrategy

class ExecutivePolicyEngine:
    """
    Lightweight decision layer that determines when executive collaboration is required,
    which executives should participate, and which decision strategy to apply.
    """

    @staticmethod
    def requires_executive_council(plan: ExecutionPlan) -> bool:
        """
        Determines if the objective requires an executive council.
        Uses task complexity and the presence of multiple specialized executive capabilities.
        """
        if not plan or not plan.tasks:
            return False
            
        high_complexity_tasks = [t for t in plan.tasks if getattr(t, "complexity", 1.0) >= 7.0]
        executive_agents = {t.assigned_agent for t in plan.tasks if t.assigned_agent and t.assigned_agent not in ["Knowledge Agent", "ResearchAgent"]}
        
        # If there are high complexity tasks or multiple executives involved, use the council.
        if len(high_complexity_tasks) > 0 or len(executive_agents) > 1:
            return True
            
        return False

    @staticmethod
    def determine_decision_strategy(plan: ExecutionPlan) -> DecisionStrategy:
        """
        Determines the appropriate decision strategy based on the execution plan.
        """
        high_complexity_tasks = [t for t in plan.tasks if getattr(t, "complexity", 1.0) >= 8.5]
        
        # If it's highly complex, CEO override is usually standard for final veto.
        if len(high_complexity_tasks) > 0:
            return DecisionStrategy.CEO_OVERRIDE
            
        return DecisionStrategy.MAJORITY_VOTE
