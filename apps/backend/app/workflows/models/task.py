from sqlalchemy import Column, String, Integer, DateTime, Float, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "Pending"
    QUEUED = "Queued"
    RUNNING = "Running"
    RETRYING = "Retrying"
    COMPLETED = "Completed"
    FAILED = "Failed"
    SKIPPED = "Skipped"
    CANCELLED = "Cancelled"


class TaskType(str, enum.Enum):
    CAPABILITY = "Capability Task"
    AGENT = "Agent Task"
    DECISION = "Decision Task"
    APPROVAL = "Approval Task"
    NOTIFICATION = "Notification Task"
    CONDITIONAL = "Conditional Task"
    PARALLEL = "Parallel Task"
    DELAY = "Delay Task"
    LOOP = "Loop Task"


class Task(Base):
    __tablename__ = "workflow_tasks"

    task_id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=True)  # Multi-tenancy
    workflow_id = Column(String, ForeignKey("workflows.workflow_id"), nullable=False)

    task_type = Column(Enum(TaskType), default=TaskType.CAPABILITY)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)

    assigned_agent = Column(String, nullable=True)
    required_capability = Column(String, nullable=True)

    dependencies = Column(JSON, default=list)  # List of task_ids this task depends on

    retry_policy = Column(JSON, default=dict)
    timeout = Column(Integer, nullable=True)  # Timeout in seconds

    inputs = Column(JSON, default=dict)
    outputs = Column(JSON, default=dict)
    artifacts = Column(JSON, default=dict)

    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    error = Column(String, nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)  # Execution time in milliseconds

    workflow = relationship("Workflow", back_populates="tasks")
