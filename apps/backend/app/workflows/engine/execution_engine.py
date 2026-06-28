from typing import Any, Dict
import logging
from app.workflows.models.task import Task, TaskType
from app.workflows.context.workflow_context import WorkflowContext

logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self, governance_pipeline=None):
        # In a real system, this would map capabilities to their executor functions
        self.capability_registry = {}
        self.governance_pipeline = governance_pipeline
        
    def register_capability(self, name: str, executor_fn: Any):
        self.capability_registry[name] = executor_fn

    async def execute_task(self, task: Task, context: WorkflowContext) -> Dict[str, Any]:
        """Execute a single task based on its type."""
        logger.info(f"Executing task {task.task_id} of type {task.task_type}")
        
        # Merge context variables into task inputs if needed
        # For simplicity, we just pass the context
        
        if task.task_type == TaskType.CAPABILITY:
            return await self._execute_capability(task, context)
        elif task.task_type == TaskType.DECISION:
            return await self._execute_decision(task, context)
        elif task.task_type == TaskType.AGENT:
            return await self._execute_agent(task, context)
        else:
            logger.warning(f"Unsupported task type: {task.task_type}")
            return {"status": "skipped", "reason": "unsupported type"}

    async def _execute_capability(self, task: Task, context: WorkflowContext) -> Dict[str, Any]:
        if not task.required_capability:
            raise ValueError(f"Task {task.task_id} requires a capability but none was provided.")
            
        # 1. Run Governance
        if self.governance_pipeline:
            from app.governance.context.governance_context import GovernanceContext
            gov_context = GovernanceContext(
                workflow_id=context.workflow_id,
                task_id=task.task_id,
                capability_name=task.required_capability,
                workflow_goal=context.get_variable("workflow_goal", ""),
                task_description=task.description,
                executive_agent=task.assigned_agent
            )
            decision = self.governance_pipeline.evaluate(gov_context)
            
            if decision.blocked or decision.approval_required:
                # We return the state so the scheduler can handle it instead of an exception
                return {
                    "status": "governance_intervention",
                    "next_state": decision.next_state,
                    "reason": decision.reason,
                    "decision": decision.dict()
                }

        # 2. Capability Execution
        executor = self.capability_registry.get(task.required_capability)
        if not executor:
            logger.warning(f"Capability {task.required_capability} not found. Mocking success.")
            return {"mock_result": f"Executed {task.required_capability}"}
            
        # In production, we'd actually call it:
        # return await executor(task.inputs, context)
        return {"mock_result": f"Executed {task.required_capability}"}

    async def _execute_decision(self, task: Task, context: WorkflowContext) -> Dict[str, Any]:
        # Evaluates a condition based on context variables
        return {"decision": True}

    async def _execute_agent(self, task: Task, context: WorkflowContext) -> Dict[str, Any]:
        # Invokes a specialized agent (like CTO) to perform reasoning
        return {"agent_output": "Completed analysis"}
