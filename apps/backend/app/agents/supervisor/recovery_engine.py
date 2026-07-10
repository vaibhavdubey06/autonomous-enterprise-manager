import logging
from typing import Dict, Any
from app.agents.supervisor.schemas import SupervisorState, TaskStatus

logger = logging.getLogger(__name__)


class RecoveryStrategy:
    def execute(self, state: SupervisorState) -> SupervisorState:
        raise NotImplementedError


class RetryStrategy(RecoveryStrategy):
    def execute(self, state: SupervisorState) -> SupervisorState:
        logger.info("[RecoveryEngine] Executing RetryStrategy")
        # Reset failed tasks to PENDING
        failed_task_ids = state.get("failed_tasks", [])
        if state.get("execution_plan"):
            for t in state["execution_plan"].tasks:
                if t.task_id in failed_task_ids:
                    t.status = TaskStatus.PENDING

        # Clear failed tasks so they can be retried
        state["failed_tasks"] = []
        state["recovery_cycles"] = state.get("recovery_cycles", 0) + 1
        state["last_recovery_strategy"] = "RetryStrategy"
        return state


class ReplanStrategy(RecoveryStrategy):
    def execute(self, state: SupervisorState) -> SupervisorState:
        logger.info("[RecoveryEngine] Executing ReplanStrategy")
        state["replan_count"] = state.get("replan_count", 0) + 1
        state["recovery_cycles"] = state.get("recovery_cycles", 0) + 1
        state["last_recovery_strategy"] = "ReplanStrategy"
        return state


class EscalateStrategy(RecoveryStrategy):
    def execute(self, state: SupervisorState) -> SupervisorState:
        logger.info("[RecoveryEngine] Executing EscalateStrategy")
        state["workflow_state"] = "Failed"
        return state


class SkipOptionalStrategy(RecoveryStrategy):
    def execute(self, state: SupervisorState) -> SupervisorState:
        logger.info("[RecoveryEngine] Executing SkipOptionalStrategy")
        failed_task_ids = state.get("failed_tasks", [])
        # Move failed tasks to completed (skipping them)
        state["completed_tasks"].extend(failed_task_ids)
        state["failed_tasks"] = []
        state["recovery_cycles"] = state.get("recovery_cycles", 0) + 1
        state["last_recovery_strategy"] = "SkipOptionalStrategy"
        return state


class RecoveryEngine:
    """
    Registry-based recovery engine. Selects a strategy to mutate state
    to recover from execution monitor flags.
    """

    def __init__(self, decision_engine=None):
        self.strategies = {
            "RETRY": RetryStrategy(),
            "REPLAN": ReplanStrategy(),
            "ESCALATE": EscalateStrategy(),
            "SKIP_OPTIONAL": SkipOptionalStrategy(),
        }
        from app.services.decisions.engine import DecisionEngine

        self.decision_engine = decision_engine or DecisionEngine()

    def trigger_recovery(
        self, state: SupervisorState, diagnosis: Dict[str, Any]
    ) -> SupervisorState:
        reason = diagnosis.get("reason")
        failed_tasks = diagnosis.get("failed_tasks", [])

        if failed_tasks:
            state["last_failed_task"] = failed_tasks[0]

        logger.warning(f"[RecoveryEngine] Triggered for reason: {reason}")

        # Determine strategy
        # For simplicity, if Autonomy Level is high, we REPLAN. Otherwise RETRY.
        # If it's a timeout, ESCALATE.
        autonomy_level = state.get("autonomy_level", 2)

        strategy_name = "RETRY"
        if reason == "SLA_TIMEOUT":
            strategy_name = "ESCALATE"
        elif reason == "TASK_FAILURE" and autonomy_level >= 3:  # Auto Recover
            # Check if we already retried this
            if state.get("last_recovery_strategy") == "RetryStrategy":
                strategy_name = "REPLAN"
            else:
                strategy_name = "RETRY"
        elif reason == "TASK_FAILURE" and autonomy_level < 3:
            strategy_name = "ESCALATE"  # Cannot auto-recover

        strategy = self.strategies.get(strategy_name, EscalateStrategy())

        from app.services.decisions.models import DecisionType

        self.decision_engine.record_decision(
            decision_type=DecisionType.RECOVERY,
            component="RecoveryEngine",
            selected_option=strategy_name,
            context={
                "failure_reason": reason,
                "recovery_cycles": state.get("recovery_cycles", 0),
            },
            trace_id=state.get("trace_id"),
        )

        return strategy.execute(state)
