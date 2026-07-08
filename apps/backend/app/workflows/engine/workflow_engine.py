import asyncio
import logging
from app.workflows.engine.scheduler import WorkflowScheduler
from app.workflows.repositories.workflow_repository import WorkflowRepository
from app.workflows.events.in_memory_event_bus import InMemoryEventBus
from app.workflows.engine.execution_engine import ExecutionEngine
from app.workflows.models.workflow import WorkflowStatus
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class WorkflowEngine:
    def __init__(self, db: Session):
        self.repository = WorkflowRepository(db)
        self.event_bus = InMemoryEventBus()
        self.execution_engine = ExecutionEngine()
        self.scheduler = WorkflowScheduler(
            self.repository, self.event_bus, self.execution_engine
        )

    async def start_workflow(self, workflow_id: str) -> None:
        """Starts a workflow execution in the background."""
        workflow = self.repository.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if workflow.status not in (
            WorkflowStatus.DRAFT,
            WorkflowStatus.PLANNED,
            WorkflowStatus.READY,
        ):
            raise ValueError(
                f"Workflow {workflow_id} is in status {workflow.status} and cannot be started"
            )

        logger.info(f"Submitting workflow {workflow_id} for execution")
        # Start in background
        asyncio.create_task(self._run_and_memorize(workflow_id))

    async def _run_and_memorize(self, workflow_id: str) -> None:
        await self.scheduler.run_workflow(workflow_id)

        # After completion, check if it was successful and extract memory
        workflow = self.repository.get_workflow(workflow_id)
        if workflow and workflow.status == WorkflowStatus.COMPLETED:
            try:
                from app.services.memory_service import MemoryService
                from app.repositories.session_repository import SessionRepository
                from app.repositories.conversation_repository import (
                    ConversationRepository,
                )
                from app.repositories.message_repository import MessageRepository
                from app.repositories.summary_repository import SummaryRepository
                from app.repositories.memory_repository import MemoryRepository
                from app.services.llm.gateway import LLMGateway

                db = self.repository.db
                memory_service = MemoryService(
                    SessionRepository(db),
                    ConversationRepository(db),
                    MessageRepository(db),
                    SummaryRepository(db),
                    MemoryRepository(db),
                    LLMGateway(),
                )

                # We format the goal and the result context to let the LLM extract structured memory
                goal = workflow.goal
                result_str = str(workflow.workflow_metadata)

                logger.info(
                    f"Extracting cognitive memory for completed workflow {workflow_id}"
                )
                await memory_service.extract_and_store_memories(
                    conversation_id=workflow_id,
                    user_id=workflow.initiated_by or "system",
                    user_message=f"Workflow Goal: {goal}",
                    assistant_response=f"Workflow Completed. Results: {result_str}",
                )
            except Exception as e:
                logger.error(
                    f"Failed to extract memory for workflow {workflow_id}: {e}",
                    exc_info=True,
                )

    def pause_workflow(self, workflow_id: str) -> None:
        self.repository.update_workflow_status(workflow_id, WorkflowStatus.PAUSED)

    def cancel_workflow(self, workflow_id: str) -> None:
        self.repository.update_workflow_status(workflow_id, WorkflowStatus.CANCELLED)
