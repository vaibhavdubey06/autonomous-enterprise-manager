from typing import List, Dict, Any
import uuid
from app.workflows.schemas.workflow import WorkflowCreate, WorkflowSchema, TaskSchema
from app.workflows.engine.dependency_resolver import DependencyResolver
from app.workflows.models.task import TaskType


class WorkflowBuilder:
    def __init__(self, workflow_create: WorkflowCreate):
        self.workflow_id = str(uuid.uuid4())
        self.goal = workflow_create.goal
        self.description = workflow_create.description
        self.owner_agent = workflow_create.owner_agent
        self.initiated_by = workflow_create.initiated_by
        self.template_name = workflow_create.template_name
        self.approval_required = workflow_create.approval_required
        self.priority = workflow_create.priority
        self.tasks: List[TaskSchema] = []

    def add_task(
        self,
        name: str,
        task_type: TaskType = TaskType.CAPABILITY,
        description: str = None,
        assigned_agent: str = None,
        required_capability: str = None,
        dependencies: List[str] = None,
        inputs: Dict[str, Any] = None,
        retry_policy: Dict[str, Any] = None,
        timeout: int = None,
    ) -> str:

        task_id = str(uuid.uuid4())
        task = TaskSchema(
            task_id=task_id,
            workflow_id=self.workflow_id,
            task_type=task_type,
            name=name,
            description=description,
            assigned_agent=assigned_agent,
            required_capability=required_capability,
            dependencies=dependencies or [],
            inputs=inputs or {},
            retry_policy=retry_policy or {},
            timeout=timeout,
        )
        self.tasks.append(task)
        return task_id

    def build(self) -> WorkflowSchema:
        # Validate dependencies exist and form a DAG
        task_ids = {t.task_id for t in self.tasks}
        for t in self.tasks:
            for dep in t.dependencies:
                if dep not in task_ids:
                    raise ValueError(f"Task {t.task_id} depends on unknown task {dep}")

        # DependencyResolver uses SQLAlchemy Tasks typically, but we can duck-type or convert
        # For simplicity in building, we just use the schema for cycle detection
        class DummyTask:
            def __init__(self, t_id, deps):
                self.task_id = t_id
                self.dependencies = deps

        dummies = [DummyTask(t.task_id, t.dependencies) for t in self.tasks]
        DependencyResolver.validate_dag(dummies)

        workflow = WorkflowSchema(
            workflow_id=self.workflow_id,
            goal=self.goal,
            description=self.description,
            owner_agent=self.owner_agent,
            initiated_by=self.initiated_by,
            template_name=self.template_name,
            approval_required=self.approval_required,
            priority=self.priority,
            tasks=self.tasks,
        )
        return workflow
