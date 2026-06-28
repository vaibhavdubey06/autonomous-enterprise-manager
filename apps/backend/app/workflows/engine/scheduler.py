import asyncio
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.workflows.models.workflow import Workflow, WorkflowStatus
from app.workflows.models.task import Task, TaskStatus
from app.workflows.engine.dependency_resolver import DependencyResolver
from app.workflows.engine.execution_engine import ExecutionEngine
from app.workflows.engine.retry_manager import RetryManager
from app.workflows.context.workflow_context import WorkflowContext
from app.workflows.metrics.collector import MetricsCollector
from app.workflows.repositories.workflow_repository import WorkflowRepository
from app.workflows.events.base_event_bus import BaseEventBus
from app.workflows.events.events import (
    WorkflowEvent, WORKFLOW_STARTED, WORKFLOW_COMPLETED, WORKFLOW_FAILED,
    TASK_STARTED, TASK_COMPLETED, TASK_FAILED
)

logger = logging.getLogger(__name__)

class WorkflowScheduler:
    def __init__(self, 
                 repository: WorkflowRepository,
                 event_bus: BaseEventBus,
                 execution_engine: ExecutionEngine):
        self.repository = repository
        self.event_bus = event_bus
        self.execution_engine = execution_engine
        
    async def run_workflow(self, workflow_id: str) -> None:
        logger.info(f"Starting workflow {workflow_id}")
        
        workflow = self.repository.get_workflow(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return
            
        self.repository.update_workflow_status(workflow_id, WorkflowStatus.RUNNING)
        self.event_bus.publish(WorkflowEvent(
            event_id=f"evt_{workflow_id}_start",
            event_type=WORKFLOW_STARTED,
            workflow_id=workflow_id
        ))
        
        context = WorkflowContext(workflow_id)
        metrics = MetricsCollector()
        
        completed_task_ids = set()
        failed = False
        
        # Reload tasks explicitly to ensure session state is clean
        tasks = workflow.tasks
        
        while len(completed_task_ids) < len(tasks) and not failed:
            executable_tasks = DependencyResolver.get_executable_tasks(tasks, completed_task_ids)
            
            if not executable_tasks and len(completed_task_ids) < len(tasks):
                # We have tasks left but none are executable (cycle or failed dependencies)
                logger.error("Deadlock or unresolved dependencies detected during execution")
                failed = True
                break
                
            # Execute all independent tasks in parallel
            execution_coros = []
            for task in executable_tasks:
                if task.status in (TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RETRYING):
                    execution_coros.append(self._run_task(task, context, metrics))
                    
            if execution_coros:
                results = await asyncio.gather(*execution_coros, return_exceptions=True)
                
                for task, result in zip(executable_tasks, results):
                    if isinstance(result, Exception):
                        logger.error(f"Task {task.task_id} completely failed: {result}")
                        self.repository.update_task_status(task.task_id, TaskStatus.FAILED, str(result))
                        failed = True
                    elif isinstance(result, dict) and result.get("status") == "governance_intervention":
                        logger.warning(f"Task {task.task_id} blocked by governance. Next state: {result.get('next_state')}")
                        self.repository.update_workflow_status(workflow_id, result.get("next_state"))
                        failed = True # Halt loop for now, we will await human approval
                        break
                    else:
                        completed_task_ids.add(task.task_id)
                        
            # Prevent tight loops if nothing executed (should not happen due to deadlock check)
            if not execution_coros:
                await asyncio.sleep(0.1)
                
        # Finalize Workflow
        if failed:
            current_status = self.repository.get_workflow(workflow_id).status
            if current_status not in [WorkflowStatus.WAITING_FOR_APPROVAL, WorkflowStatus.WAITING_FOR_GOVERNANCE, WorkflowStatus.BLOCKED]:
                self.repository.update_workflow_status(workflow_id, WorkflowStatus.FAILED)
                self.event_bus.publish(WorkflowEvent(
                    event_id=f"evt_{workflow_id}_failed",
                    event_type=WORKFLOW_FAILED,
                    workflow_id=workflow_id
                ))
            else:
                logger.info(f"Workflow {workflow_id} paused in state {current_status}")
        else:
            workflow = self.repository.update_workflow_status(workflow_id, WorkflowStatus.COMPLETED)
            workflow.execution_metrics = metrics.complete_workflow()
            workflow.workflow_metadata = context.get_all_state()
            self.repository.db.commit()
            
            self.event_bus.publish(WorkflowEvent(
                event_id=f"evt_{workflow_id}_completed",
                event_type=WORKFLOW_COMPLETED,
                workflow_id=workflow_id
            ))
            
    async def _run_task(self, task: Task, context: WorkflowContext, metrics: MetricsCollector) -> Any:
        self.repository.update_task_status(task.task_id, TaskStatus.RUNNING)
        metrics.record_task_start(task.task_id)
        
        self.event_bus.publish(WorkflowEvent(
            event_id=f"evt_{task.task_id}_start",
            event_type=TASK_STARTED,
            workflow_id=task.workflow_id,
            task_id=task.task_id
        ))
        
        try:
            # We use RetryManager to wrap the execution
            async def _exec_wrapper(t):
                return await self.execution_engine.execute_task(t, context)
                
            outputs = await RetryManager.execute_with_retry(task, _exec_wrapper)
            
            # Save outputs to context and repository
            context.set_task_output(task.task_id, outputs)
            self.repository.update_task(task.task_id, {"outputs": outputs, "status": TaskStatus.COMPLETED})
            metrics.record_task_end(task.task_id, "Completed")
            
            self.event_bus.publish(WorkflowEvent(
                event_id=f"evt_{task.task_id}_completed",
                event_type=TASK_COMPLETED,
                workflow_id=task.workflow_id,
                task_id=task.task_id,
                payload=outputs
            ))
            return outputs
            
        except Exception as e:
            metrics.record_task_end(task.task_id, "Failed")
            self.event_bus.publish(WorkflowEvent(
                event_id=f"evt_{task.task_id}_failed",
                event_type=TASK_FAILED,
                workflow_id=task.workflow_id,
                task_id=task.task_id,
                payload={"error": str(e)}
            ))
            raise e
