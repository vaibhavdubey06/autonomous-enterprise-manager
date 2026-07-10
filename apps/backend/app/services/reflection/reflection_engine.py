import logging
from typing import Dict, Any
from app.operations.tracing.trace_manager import TraceManager
from app.agents.supervisor.schemas import SupervisorState

logger = logging.getLogger(__name__)


class ReflectionEngine:
    """
    Evaluates completed or failed workflows, analyzes traces, and extracts
    operational lessons. Stores insights for the WorkflowOptimizer.
    """

    def __init__(self):
        self.trace_manager = TraceManager()

    def reflect_on_workflow(self, state: SupervisorState) -> Dict[str, Any]:
        """
        Analyzes the final state of the SupervisorGraph, the execution trace,
        task results, and failures to produce reflections.
        """
        logger.info(
            f"ReflectionEngine analyzing workflow: {state.get('goal', 'Unknown')}"
        )

        reflections = {
            "success": not bool(state.get("failed_tasks")),
            "agent_performance": self._analyze_agents(state),
            "planning_accuracy": self._analyze_planning(state),
            "recovery_effectiveness": self._analyze_recovery(state),
            "heuristics": [],
        }

        # Generate specific heuristics to feed the optimizer
        if reflections["success"]:
            reflections["heuristics"].append(
                f"Successfully used agents {list(reflections['agent_performance'].keys())} for goal containing '{state.get('goal', '')[:20]}'"
            )
        else:
            if state.get("failed_tasks"):
                reflections["heuristics"].append(
                    f"Task failure detected on nodes: {state.get('failed_tasks')}"
                )

        # Send telemetry for evaluation engine
        self._record_telemetry(reflections)

        return reflections

    def _analyze_agents(self, state: SupervisorState) -> Dict[str, Any]:
        """Calculates success rates per agent."""
        perf = {}
        for res in state.get("task_results", []):
            agent = res.get("agent_used", "Unknown")
            is_success = not res.get("result", "").startswith("Execution failed")
            if agent not in perf:
                perf[agent] = {"success": 0, "fail": 0}
            if is_success:
                perf[agent]["success"] += 1
            else:
                perf[agent]["fail"] += 1
        return perf

    def _analyze_planning(self, state: SupervisorState) -> Dict[str, Any]:
        plan = state.get("execution_plan")
        return {
            "tasks_planned": len(plan.tasks) if plan else 0,
            "tasks_completed": len(state.get("completed_tasks", [])),
            "replan_count": state.get("replan_count", 0),
        }

    def _analyze_recovery(self, state: SupervisorState) -> Dict[str, Any]:
        return {
            "recovery_cycles": state.get("recovery_cycles", 0),
            "last_strategy": state.get("last_recovery_strategy"),
        }

    def _record_telemetry(self, reflections: Dict[str, Any]):
        """Records metrics for the evaluator."""
        span = self.trace_manager.start_trace("reflection_engine")
        span.attributes["success"] = reflections["success"]
        span.attributes["planning_accuracy"] = reflections["planning_accuracy"]
        self.trace_manager.end_span(span, "OK")
