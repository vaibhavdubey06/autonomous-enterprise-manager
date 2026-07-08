import logging
from typing import Dict, Any
import time

from app.agents.base.base_agent import BaseExecutiveAgent
from app.agents.base.profile import AgentProfile
from app.agents.base.capabilities import Capability
from app.agents.base.task import ExecutiveTask
from app.agents.base.output import ExecutiveResult
from app.services.llm.gateway import LLMGateway

from app.agents.executives.cto.planner import CTOPlanner
from app.agents.executives.cto.architect import ArchitectureReviewer
from app.agents.executives.cto.reviewer import TechnicalReviewer

logger = logging.getLogger(__name__)


class CTOAgent(BaseExecutiveAgent):
    """
    The Chief Technology Officer (CTO) Executive Agent.
    Specializes in software architecture, code quality, tech debt, and system design.
    """

    def __init__(
        self,
        llm_service: LLMGateway,
        capability_executor=None,
        knowledge_agent_graph=None,
    ):
        super().__init__(llm_service, capability_executor)
        self.planner = CTOPlanner(llm_service)
        self.architect = ArchitectureReviewer(llm_service)
        self.reviewer = TechnicalReviewer(llm_service)

        # Temporary for backward compatibility during migration
        self.knowledge_agent = knowledge_agent_graph

        self._profile = AgentProfile(
            agent_name="CTO Agent",
            title="Chief Technology Officer",
            domain="Engineering & Architecture",
            description="Evaluates system architecture, codebase quality, technical debt, and provides technical planning.",
            capabilities=[
                Capability.CODE_REVIEW,
                Capability.ARCHITECTURE_ANALYSIS,
                Capability.TECHNICAL_PLANNING,
                Capability.SYSTEM_DESIGN,
            ],
            supported_task_types=[
                "Architecture Review",
                "Codebase Analysis",
                "Technical Debt Analysis",
                "Migration Planning",
                "Technology Recommendation",
            ],
            required_tools=[],
            supported_sources=["GitHub", "Architecture Docs", "Technical Memory"],
            responsibilities=["Technical direction", "Architecture validation", "Engineering practices"],
            decision_authority=["Engineering standards", "Architecture patterns", "Technology stack"],
            inputs=["Technical proposals", "Codebase context", "System diagrams"],
            outputs=["Architecture review", "Technical plan", "Refactoring guide"],
            memory_requirements=["Technical memory", "Architecture decisions"],
            approval_requirements=["Requires CFO approval for major infrastructure spend"],
            escalation_rules=["Escalate to CEO for major platform shifts"],
            decision_boundaries=["Does not approve budgets"],
        )

    def get_profile(self) -> AgentProfile:
        return self._profile

    def execute(self, task: ExecutiveTask, state: Dict[str, Any]) -> ExecutiveResult:
        start_time = time.time()
        logger.info(f"[CTO Agent] Executing task via Workflow Runtime: {task.goal}")

        # We will dispatch this to the Workflow Engine
        from app.core.database import SessionLocal
        from app.workflows.services.workflow_service import WorkflowService
        from app.workflows.builder.workflow_builder import WorkflowBuilder
        from app.workflows.schemas.workflow import WorkflowCreate
        from app.workflows.models.task import TaskType
        import asyncio

        db = SessionLocal()
        try:
            workflow_service = WorkflowService(db)

            # Determine if we can use a template
            if "review" in task.goal.lower() and "repository" in task.goal.lower():
                from app.workflows.templates.repository_review import (
                    create_repository_review_workflow,
                )

                builder = create_repository_review_workflow(
                    repo_url="extract_from_state_or_goal"
                )
            else:
                # Custom Workflow
                builder = WorkflowBuilder(
                    WorkflowCreate(
                        goal=task.goal,
                        description=f"CTO Agent executing task: {task.goal}",
                        owner_agent="CTO",
                    )
                )

                # We can use the old planner to generate task dependencies
                plan = self.planner.plan(task)

                prev_deps = []
                for action in plan.required_github_actions:
                    t_id = builder.add_task(
                        name=f"GitHub Action: {action}",
                        task_type=TaskType.CAPABILITY,
                        required_capability="github_tool",
                        inputs={"action": action},
                    )
                    prev_deps.append(t_id)

                for query in plan.queries:
                    t_id = builder.add_task(
                        name=f"Knowledge Query: {query}",
                        task_type=TaskType.AGENT,
                        assigned_agent="KnowledgeAgent",
                        inputs={"query": query},
                        dependencies=prev_deps.copy(),
                    )
                    prev_deps.append(t_id)

                builder.add_task(
                    name="CTO Final Analysis",
                    task_type=TaskType.AGENT,
                    assigned_agent="CTO",
                    dependencies=prev_deps.copy(),
                )

            # Create the workflow
            workflow_schema = workflow_service.create_workflow_from_builder(builder)
            workflow_id = workflow_schema.workflow_id
            logger.info(f"Created Workflow {workflow_id} for task {task.goal}")

            # Execute workflow
            # In a real environment, we might await this or dispatch to celery.
            # If the current loop is running, we can create a task. If no loop, we run it.
            try:
                asyncio.get_running_loop()
                # Fire and forget if loop is already running (e.g. FastAPI request)
                asyncio.create_task(workflow_service.execute_workflow(workflow_id))
            except RuntimeError:
                # Run synchronously if no loop
                asyncio.run(workflow_service.execute_workflow(workflow_id))

            summary = (
                f"CTO Agent formulated Workflow {workflow_id} to achieve: '{task.goal}'"
            )

            metrics = {
                "execution_time_ms": (time.time() - start_time) * 1000,
                "workflow_id": workflow_id,
                "tasks_planned": len(builder.tasks),
            }

            return self._create_result(
                task=task,
                summary=summary,
                reasoning=f"Delegated execution to Workflow Runtime. ID: {workflow_id}",
                recommendations=[
                    f"Monitor Workflow {workflow_id} in the Workflow Dashboard"
                ],
                sources=[],
                metrics=metrics,
            )
        finally:
            db.close()
