"""Enterprise Scheduler Platform - Job scheduling and background task management."""

import logging
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class ScheduledJob:
    """Represents a scheduled job in the enterprise scheduler."""

    def __init__(
        self,
        name: str,
        handler: Callable[..., Any],
        cron_expression: Optional[str] = None,
        delay_seconds: Optional[float] = None,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.job_id = str(uuid.uuid4())
        self.name = name
        self.handler = handler
        self.cron_expression = cron_expression
        self.delay_seconds = delay_seconds
        self.priority = priority
        self.max_retries = max_retries
        self.metadata = metadata or {}
        self.status = JobStatus.PENDING
        self.created_at = time.time()
        self.last_run_at: Optional[float] = None
        self.run_count = 0
        self.failure_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "status": self.status.value,
            "priority": self.priority.value,
            "cron_expression": self.cron_expression,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at,
            "last_run_at": self.last_run_at,
        }


class SchedulerService:
    """Central scheduler service managing all background jobs."""

    def __init__(self) -> None:
        self._jobs: Dict[str, ScheduledJob] = {}
        self._retry_queue: List[ScheduledJob] = []

    def register_job(self, job: ScheduledJob) -> str:
        self._jobs[job.job_id] = job
        logger.info(f"Registered job: {job.name} ({job.job_id})")
        return job.job_id

    def execute_job(self, job_id: str) -> Dict[str, Any]:
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        job.status = JobStatus.RUNNING
        job.last_run_at = time.time()
        job.run_count += 1

        try:
            result = job.handler()
            job.status = JobStatus.COMPLETED
            return {"job_id": job_id, "status": "completed", "result": result}
        except Exception as e:
            job.failure_count += 1
            if job.failure_count < job.max_retries:
                job.status = JobStatus.PENDING
                self._retry_queue.append(job)
                logger.warning(
                    f"Job {job.name} failed, queued for retry ({job.failure_count}/{job.max_retries})"
                )
            else:
                job.status = JobStatus.FAILED
                logger.error(
                    f"Job {job.name} permanently failed after {job.max_retries} retries"
                )
            return {"job_id": job_id, "status": "failed", "error": str(e)}

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.CANCELLED
            return True
        return False

    def list_jobs(self, status: Optional[JobStatus] = None) -> List[Dict[str, Any]]:
        jobs = self._jobs.values()
        if status:
            jobs = [j for j in jobs if j.status == status]
        return [j.to_dict() for j in jobs]

    def get_retry_queue(self) -> List[Dict[str, Any]]:
        return [j.to_dict() for j in self._retry_queue]

    def process_retry_queue(self) -> List[Dict[str, Any]]:
        results = []
        while self._retry_queue:
            job = self._retry_queue.pop(0)
            result = self.execute_job(job.job_id)
            results.append(result)
        return results
