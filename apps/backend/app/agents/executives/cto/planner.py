import logging
from typing import List
from pydantic import BaseModel
from app.services.llm.llm_service import LLMService
from app.agents.executives.cto.prompts import CTO_PLANNER_PROMPT
from app.agents.base.task import ExecutiveTask

logger = logging.getLogger(__name__)

class CTOExecutionPlan(BaseModel):
    queries: List[str]
    required_github_actions: List[str] = []
    rationale: str

class CTOPlanner:
    """
    Analyzes the ExecutiveTask and determines the execution strategy, 
    including which queries need to be run against the Knowledge Agent.
    """
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def plan(self, task: ExecutiveTask) -> CTOExecutionPlan:
        prompt = CTO_PLANNER_PROMPT.format(
            goal=task.goal,
            description=task.description
        )
        logger.info("CTOPlanner generating execution plan...")
        
        try:
            json_str = self.llm_service.generate_structured(prompt, CTOExecutionPlan)
            import json
            return CTOExecutionPlan(**json.loads(json_str))
        except Exception as e:
            logger.error(f"CTOPlanner failed to generate structured plan: {e}")
            return CTOExecutionPlan(
                queries=[task.description],
                rationale="Fallback to simple task description query due to error."
            )
