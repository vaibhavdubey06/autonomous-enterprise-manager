import logging
from typing import Dict, Any
from app.agents.supervisor.schemas import SupervisorState

logger = logging.getLogger(__name__)

class ExecutionMonitor:
    """
    Observer that monitors workflow execution state, detects bottlenecks,
    and identifies when a workflow has stalled or failed.
    Does NOT orchestrate execution itself.
    """

    def check_health(self, state: SupervisorState) -> Dict[str, Any]:
        """
        Analyzes the current graph state for anomalies or failures.
        Returns a dict indicating if recovery is needed.
        """
        logger.info("[ExecutionMonitor] Checking workflow health...")
        
        failed_tasks = state.get("failed_tasks", [])
        replan_count = state.get("replan_count", 0)
        recovery_cycles = state.get("recovery_cycles", 0)
        
        # 1. Check for infinite loops
        if replan_count > 3 or recovery_cycles > 3:
            logger.error("[ExecutionMonitor] Infinite loop detected! Too many replans/recoveries.")
            return {"needs_recovery": False, "abort_workflow": True, "reason": "MAX_RECOVERY_EXCEEDED"}

        # 2. Check for task failures
        if failed_tasks:
            logger.warning(f"[ExecutionMonitor] Detected failed tasks: {failed_tasks}")
            
            # Check if this failure is identical to the last one (loop detection)
            last_failed = state.get("last_failed_task")
            if last_failed and last_failed in failed_tasks and recovery_cycles > 0:
                logger.error("[ExecutionMonitor] Identical failure loop detected.")
                return {"needs_recovery": False, "abort_workflow": True, "reason": "IDENTICAL_FAILURE_LOOP"}

            return {
                "needs_recovery": True, 
                "abort_workflow": False, 
                "failed_tasks": failed_tasks,
                "reason": "TASK_FAILURE"
            }
            
        # 3. Check for timeout / stalled (Stub for future SLA monitoring)
        execution_time_ms = state.get("execution_time_ms", 0)
        if execution_time_ms > 300000: # 5 minutes
            logger.warning("[ExecutionMonitor] Workflow SLA timeout exceeded.")
            return {"needs_recovery": True, "abort_workflow": False, "reason": "SLA_TIMEOUT"}

        return {"needs_recovery": False, "abort_workflow": False, "reason": "HEALTHY"}
