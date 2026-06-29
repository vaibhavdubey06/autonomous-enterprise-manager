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
            from pydantic import BaseModel
            from typing import List

            class LLMTask(BaseModel):
                goal: str
                description: str
                priority: int
                assigned_agent: str
                required_capabilities: List[str]
                dependencies: List[str]

            class LLMExecutionPlan(BaseModel):
                goal: str
                tasks: List[LLMTask]

            # We use LLMService's structured output capability with a schema free of defaults
            json_response = self.llm_service.generate_structured(
                prompt, LLMExecutionPlan
            )

            # Clean markdown if present
            cleaned_json = json_response.strip()
            if cleaned_json.startswith("```json"):
                cleaned_json = cleaned_json[7:]
            if cleaned_json.startswith("```"):
                cleaned_json = cleaned_json[3:]
            if cleaned_json.endswith("```"):
                cleaned_json = cleaned_json[:-3]
            cleaned_json = cleaned_json.strip()

            try:
                plan_data = json.loads(cleaned_json)
            except Exception as json_e:
                logger.error(f"Failed to parse JSON: {cleaned_json}")
                raise json_e

            # Map back to full application schema
            from app.agents.supervisor.schemas import Task, TaskStatus

            tasks = []
            for t in plan_data.get("tasks", []):
                tasks.append(
                    Task(
                        goal=t.get("goal", goal),
                        description=t.get("description", ""),
                        priority=t.get("priority", 1),
                        assigned_agent=t.get("assigned_agent", "Knowledge Agent"),
                        required_capabilities=t.get("required_capabilities", []),
                        dependencies=t.get("dependencies", []),
                        status=TaskStatus.PENDING,
                    )
                )

            return ExecutionPlan(goal=plan_data.get("goal", goal), tasks=tasks)
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
                        assigned_agent="Knowledge Agent",
                    )
                ],
            )
