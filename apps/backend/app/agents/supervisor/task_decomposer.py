import logging
from typing import List
from app.agents.supervisor.schemas import ExecutionPlan, Task, TaskStatus

logger = logging.getLogger(__name__)


class TaskDecomposer:
    """
    Takes a high-level execution plan or complex goal and ensures it is split
    into a sequence of actionable Task objects with correct dependencies.
    """

    def decompose(self, plan: ExecutionPlan) -> List[Task]:
        """
        Decomposes the ExecutionPlan into a list of Tasks.
        Ensures tasks are sequentially dependent if not explicitly specified.
        """
        tasks = plan.tasks

        logger.info(f"TaskDecomposer processing {len(tasks)} tasks from plan.")

        if not tasks:
            return []

        # Basic validation and sequential dependency mapping
        for i, task in enumerate(tasks):
            task.status = TaskStatus.PENDING

            # If no dependencies are explicitly defined, assume sequential execution
            if i > 0 and not task.dependencies:
                # Depend on the previous task's ID
                task.dependencies.append(tasks[i - 1].task_id)

        return tasks
