import logging
import time
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.supervisor.schemas import SupervisorState
from app.agents.supervisor.planner import Planner
from app.agents.supervisor.task_decomposer import TaskDecomposer
from app.agents.supervisor.router import AgentRouter
from app.agents.supervisor.execution_monitor import ExecutionMonitor
from app.agents.supervisor.recovery_engine import RecoveryEngine
from app.services.reflection.workflow_optimizer import WorkflowOptimizer
from app.services.memory_service import MemoryService
from app.workflows.engine.execution_scheduler import ExecutionScheduler
from app.workflows.engine.result_aggregator import ResultAggregator
from app.operations.tracing.trace_manager import TraceManager
import asyncio

logger = logging.getLogger(__name__)


class SupervisorGraph:
    """
    The orchestrator graph for the Enterprise CEO Agent.
    Now operates as a cyclic, autonomous state machine.
    """

    def __init__(
        self,
        planner: Planner,
        task_decomposer: TaskDecomposer,
        agent_router: AgentRouter,
        memory_service: MemoryService | None = None,
        collaboration_manager=None,
    ):
        self.planner = planner
        self.task_decomposer = task_decomposer
        self.agent_router = agent_router
        self.memory_service = memory_service
        self.collaboration_manager = collaboration_manager

        self.execution_monitor = ExecutionMonitor()
        self.recovery_engine = RecoveryEngine()
        self.optimizer = WorkflowOptimizer()

        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(SupervisorState)

        # Nodes
        builder.add_node("understand_goal", self.understand_goal)
        builder.add_node("planning", self.planning)
        builder.add_node("task_decomposition", self.task_decomposition)
        builder.add_node("dependency_analysis", self.dependency_analysis)
        builder.add_node("route_and_execute", self.route_and_execute)
        builder.add_node("monitor_execution", self.monitor_execution)
        builder.add_node("recover", self.recover)
        builder.add_node("merge_results", self.merge_results)
        builder.add_node("optimize", self.optimize)

        # Edges
        builder.set_entry_point("understand_goal")
        builder.add_edge("understand_goal", "planning")
        builder.add_edge("planning", "task_decomposition")
        builder.add_edge("task_decomposition", "dependency_analysis")
        builder.add_edge("dependency_analysis", "route_and_execute")
        builder.add_edge("route_and_execute", "monitor_execution")

        # Conditional Edge from monitor_execution
        builder.add_conditional_edges(
            "monitor_execution",
            self._route_from_monitor,
            {
                "continue": "merge_results",
                "recover": "recover",
                "abort": "merge_results",
            },
        )

        # Conditional Edge from recover
        builder.add_conditional_edges(
            "recover",
            self._route_from_recovery,
            {
                "retry": "route_and_execute",
                "replan": "planning",
                "escalate": "merge_results",
            },
        )

        builder.add_edge("merge_results", "optimize")
        builder.add_edge("optimize", END)

        return builder.compile(checkpointer=self.checkpointer)

    def _route_from_monitor(self, state: SupervisorState) -> str:
        if state.get("workflow_state") == "AWAITING_RECOVERY":
            return "recover"
        elif state.get("workflow_state") == "FAILED":
            return "abort"
        return "continue"

    def _route_from_recovery(self, state: SupervisorState) -> str:
        last_strategy = state.get("last_recovery_strategy", "")
        if last_strategy == "RetryStrategy":
            return "retry"
        elif last_strategy == "ReplanStrategy":
            return "replan"
        return "escalate"

    def understand_goal(self, state: SupervisorState) -> dict:
        goal = state.get("user_input", "")
        logger.info("[Supervisor] Understanding goal: %s", goal)
        return {"goal": goal, "execution_time_ms": 0.0, "workflow_state": "Planning"}

    def planning(self, state: SupervisorState) -> dict:
        start_time = time.time()
        goal = state.get("goal", "")
        conversation_id = state.get("conversation_id")
        state.get("replan_count", 0)

        memory_context = ""
        if self.memory_service and conversation_id:
            memory_context = self.memory_service.build_memory_context(conversation_id)

        # Inject heuristics from optimizer
        heuristics = self.optimizer.get_heuristics_for_planner()
        if heuristics:
            memory_context = f"{memory_context}\n\n{heuristics}"

        plan = self.planner.plan(goal=goal, context=memory_context)
        use_collaboration = (
            len(plan.tasks) > 1
            or len({task.assigned_agent for task in plan.tasks if task.assigned_agent})
            > 1
        )

        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "memory_context": memory_context,
            "execution_plan": plan,
            "use_collaboration": use_collaboration,
            "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed_ms,
            "autonomy_level": plan.autonomy_level,
            "workflow_state": "Planned",
        }

    def task_decomposition(self, state: SupervisorState) -> dict:
        start_time = time.time()
        plan = state.get("execution_plan")
        if plan:
            self.task_decomposer.decompose(plan)
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "execution_plan": plan,
            "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed_ms,
        }

    def dependency_analysis(self, state: SupervisorState) -> dict:
        start_time = time.time()
        plan = state.get("execution_plan")
        if plan and plan.tasks:
            ExecutionScheduler.schedule(plan.tasks)
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "execution_plan": plan,
            "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed_ms,
        }

    async def route_and_execute(self, state: SupervisorState) -> dict:
        start_time = time.time()
        plan = state.get("execution_plan")
        selected_agents = state.get("selected_agents", [])
        completed_tasks = state.get("completed_tasks", [])
        failed_tasks = state.get("failed_tasks", [])
        results = state.get("task_results", [])
        trace_id = state.get("conversation_id", "workflow_trace")
        trace_manager = TraceManager()

        if plan and plan.tasks:
            groups = {}
            for task in plan.tasks:
                if (
                    task.task_id not in completed_tasks
                    and task.task_id not in failed_tasks
                ):
                    grp = getattr(task, "execution_group", 0)
                    groups.setdefault(grp, []).append(task)

            use_collaboration = state.get("use_collaboration", False)

            for grp_id in sorted(groups.keys()):
                group_tasks = groups[grp_id]

                async with asyncio.TaskGroup() as tg:
                    tasks_to_await = []
                    for task in group_tasks:

                        async def run_task(t, s):
                            capabilities_str = (
                                ",".join(
                                    str(c) for c in (t.required_capabilities or [])
                                )
                                or "None"
                            )
                            try:
                                with trace_manager.span(
                                    trace_id=trace_id,
                                    operation=f"parallel_branch_{t.task_id}",
                                    agent_name=t.assigned_agent or "Knowledge Agent",
                                    capabilities=capabilities_str,
                                    execution_stage=t.execution_group,
                                    execution_mode=(
                                        "collaboration"
                                        if use_collaboration
                                        else "direct"
                                    ),
                                ):
                                    res = self.agent_router.route_and_execute(
                                        t, dict(s), use_collaboration=use_collaboration
                                    )
                                    return res
                            except Exception as e:
                                logger.error(
                                    f"Task {t.task_id} failed with exception: {e}"
                                )
                                return {
                                    "task_id": t.task_id,
                                    "agent_used": t.assigned_agent or "Unknown",
                                    "result": f"Execution failed ({t.execution_policy}): {str(e)}",
                                    "sources": [],
                                    "metrics": {},
                                    "policy": getattr(
                                        t, "execution_policy", "CONTINUE"
                                    ),
                                }

                        tasks_to_await.append(tg.create_task(run_task(task, state)))

                for t in tasks_to_await:
                    res = t.result()
                    agent = res.get("agent_used")
                    if agent and agent not in selected_agents:
                        selected_agents.append(agent)
                    task_id = res.get("task_id")
                    policy = res.get("policy", "CONTINUE")

                    if res.get("result", "").startswith("Execution failed"):
                        failed_tasks.append(task_id)
                        if policy == "ABORT":
                            logger.error(f"Task {task_id} failed with ABORT policy.")
                            # Yield to monitor
                            return {
                                "selected_agents": selected_agents,
                                "failed_tasks": failed_tasks,
                                "task_results": results + [res],
                                "workflow_state": "Executing",
                            }
                    else:
                        completed_tasks.append(task_id)
                    results.append(res)

        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "selected_agents": selected_agents,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed_ms,
            "task_results": results,
            "workflow_state": "Executing",
        }

    def monitor_execution(self, state: SupervisorState) -> dict:
        health = self.execution_monitor.check_health(state)

        if health["abort_workflow"]:
            return {"workflow_state": "FAILED"}

        if health["needs_recovery"]:
            # Store the health diagnosis in state temporarily or infer from state later
            return {"workflow_state": "AWAITING_RECOVERY", "monitor_diagnosis": health}

        return {"workflow_state": "COMPLETED"}

    def recover(self, state: SupervisorState) -> dict:
        diagnosis = state.get("monitor_diagnosis", {})
        return self.recovery_engine.trigger_recovery(state, diagnosis)

    def merge_results(self, state: SupervisorState) -> dict:
        start_time = time.time()
        temp_results = state.get("task_results", [])
        executive_decision = state.get("executive_decision")
        plan = state.get("execution_plan")
        tasks = plan.tasks if plan else []
        goal = state.get("goal", state.get("user_input", ""))

        if executive_decision:
            aggregated_text = f"### Executive Council Recommendation\n**Strategy:** {executive_decision.get('decision_strategy')}\n"
        else:
            aggregated_text = ResultAggregator.aggregate(temp_results, tasks)

        if state.get("workflow_state") == "FAILED":
            aggregated_text = f"WORKFLOW FAILED\n\n{aggregated_text}"

        if self.planner.llm_service and (temp_results or executive_decision):
            system_prompt = "You are the Enterprise CEO Agent. Synthesize a single, cohesive response."
            prompt = f"Goal: {goal}\n\n{aggregated_text}"
            try:
                from app.services.llm.models import LLMRequest, LLMConfig
                import concurrent.futures

                request = LLMRequest(
                    prompt=f"{system_prompt}\n\n{prompt}", config=LLMConfig()
                )
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self.planner.llm_service.generate, request)
                    resp = future.result(timeout=60)
                final_response = resp.content
            except Exception as e:
                logger.error(f"LLM synthesis failed: {e}")
                final_response = aggregated_text
        else:
            final_response = aggregated_text

        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "final_response": final_response,
            "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed_ms,
        }

    def optimize(self, state: SupervisorState) -> dict:
        """Run workflow optimizer after completion."""
        self.optimizer.optimize_from_state(state)
        return {"workflow_state": "CHECKPOINT_SAVED"}

    async def run(self, initial_state: SupervisorState) -> dict:
        logger.info("Starting Supervisor Graph execution...")
        import uuid
        thread_id = f"{initial_state.get('conversation_id', 'default_thread')}_{uuid.uuid4()}"
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        final_state = await self.graph.ainvoke(initial_state, config=config)
        logger.info(
            "Supervisor Graph completed in %.2fms",
            final_state.get("execution_time_ms", 0),
        )
        return final_state
