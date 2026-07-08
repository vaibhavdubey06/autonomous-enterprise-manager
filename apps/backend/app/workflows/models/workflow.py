from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Enum
from sqlalchemy.orm import relationship, Mapped
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.workflows.models.task import Task
import enum
import datetime
from app.core.database import Base


class WorkflowStatus(str, enum.Enum):
    PLANNING = "Planning"
    EXECUTING = "Executing"
    WAITING = "Waiting"
    RECOVERING = "Recovering"
    REPLANNING = "Replanning"
    PAUSED = "Paused"
    AWAITING_APPROVAL = "Awaiting Approval"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    CHECKPOINT_SAVED = "Checkpoint Saved"
    CHECKPOINT_RESTORED = "Checkpoint Restored"
    # Legacy fallbacks for backward compatibility
    DRAFT = "Draft"
    PLANNED = "Planned"
    READY = "Ready"
    RUNNING = "Running"
    WAITING_FOR_GOVERNANCE = "WaitingForGovernance"
    WAITING_FOR_APPROVAL = "WaitingForApproval"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    BLOCKED = "Blocked"
    RESUMED = "Resumed"
    RETRYING = "Retrying"


class Workflow(Base):
    __tablename__ = "workflows"

    workflow_id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=True)  # Multi-tenancy
    workflow_version = Column(Integer, default=1)
    template_name = Column(String, nullable=True)
    template_version = Column(Integer, nullable=True)

    goal = Column(String, nullable=False)
    description = Column(String, nullable=True)

    owner_agent = Column(String, nullable=True)
    initiated_by = Column(String, nullable=True)
    priority = Column(Integer, default=0)

    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT)

    approval_required = Column(Boolean, default=False)

    workflow_metadata = Column(JSON, default=dict)
    execution_metrics = Column(JSON, default=dict)
    audit_log = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    completed_at = Column(DateTime, nullable=True)

    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="workflow", cascade="all, delete-orphan"
    )
