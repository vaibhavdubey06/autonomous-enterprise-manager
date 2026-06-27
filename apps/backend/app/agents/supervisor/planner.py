import json
import logging
from app.services.llm.llm_service import LLMService
from app.agents.supervisor.schemas import ExecutionPlan

logger = logging.getLogger(__name__)

class Planner:
    """
    Evaluates the user objective, understands intent, determines complexity, 
    and generates a structured execution plan.
    """
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def plan(self, goal: str, context: str = "") -> ExecutionPlan:
        """
        Creates an ExecutionPlan for a given goal.
        """
        prompt = (
            "You are the Enterprise Supervisor (CEO) Agent.\n"
            "Your task is to understand the user's goal and generate a structured execution plan.\n"
            "The execution plan should consist of a series of tasks.\n"
            "Available Agents: 'CTO Agent', 'Knowledge Agent'.\n"
            "Available Capabilities (tools): 'github_tool'.\n"
            "For each task, assign an agent and specify the required_capabilities (e.g., ['github_tool']).\n"
            "Keep tasks granular and actionable.\n\n"
            f"User Goal: {goal}\n"
        )
        
        if context:
            prompt += f"Context:\n{context}\n"

        logger.info(f"Planner generating execution plan for goal: {goal}")
        
        try:
            # We use LLMService's structured output capability
            json_response = self.llm_service.generate_structured(prompt, ExecutionPlan)
            plan_data = json.loads(json_response)
            
            # The LLM output might not have task_id, the Pydantic model will generate it
            return ExecutionPlan(**plan_data)
        except Exception as e:
            logger.error(f"Planner failed to generate execution plan: {e}")
            # Fallback to a single generic task
            from app.agents.supervisor.schemas import Task, TaskStatus
            return ExecutionPlan(
                goal=goal,
                tasks=[
                    Task(
                        goal=goal,
                        description="Automatically generated fallback task",
                        status=TaskStatus.PENDING,
                        assigned_agent="Knowledge Agent"
                    )
                ]
            )
