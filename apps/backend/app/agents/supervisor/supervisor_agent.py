import logging
import time
from langgraph.graph import StateGraph, END
from app.agents.supervisor.schemas import SupervisorState
from app.agents.supervisor.planner import Planner
from app.agents.supervisor.task_decomposer import TaskDecomposer
from app.agents.supervisor.router import AgentRouter

logger = logging.getLogger(__name__)


class SupervisorGraph:
    """
    The orchestrator graph for the Enterprise CEO Agent.
    """

    def __init__(
        self,
        planner: Planner,
        task_decomposer: TaskDecomposer,
        agent_router: AgentRouter,
    ):
        self.planner = planner
        self.task_decomposer = task_decomposer
        self.agent_router = agent_router
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(SupervisorState)

        # Nodes
        builder.add_node("understand_goal", self.understand_goal)
        builder.add_node("planning", self.planning)
        builder.add_node("task_decomposition", self.task_decomposition)
        builder.add_node("route_and_execute", self.route_and_execute)
        builder.add_node("merge_results", self.merge_results)

        # Edges
        builder.set_entry_point("understand_goal")
        builder.add_edge("understand_goal", "planning")
        builder.add_edge("planning", "task_decomposition")
        builder.add_edge("task_decomposition", "route_and_execute")
        builder.add_edge("route_and_execute", "merge_results")
        builder.add_edge("merge_results", END)

        return builder.compile()

    def understand_goal(self, state: SupervisorState) -> dict:
        """
        Interprets the user objective.
        For now, we simply extract it from user_input.
        In the future, we could query memory to add context.
        """
        goal = state.get("user_input", "")
        logger.info(f"[Supervisor] Understanding goal: {goal}")
        return {"goal": goal, "execution_time_ms": 0.0}

    def planning(self, state: SupervisorState) -> dict:
        """
        Determines complexity and generates ordered tasks without executing them.
        """
        start_time = time.time()
        goal = state.get("goal", "")

        plan = self.planner.plan(goal=goal)

        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "execution_plan": plan,
            "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed_ms,
        }

    def task_decomposition(self, state: SupervisorState) -> dict:
        """
        Splits complex goals and resolves task dependencies.
        """
        start_time = time.time()
        plan = state.get("execution_plan")

        if plan:
            self.task_decomposer.decompose(plan)

        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "execution_plan": plan,
            "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed_ms,
        }

    def route_and_execute(self, state: SupervisorState) -> dict:
        """
        Iterates over tasks in the execution plan and routes them to specialist agents.
        """
        start_time = time.time()
        plan = state.get("execution_plan")

        selected_agents = state.get("selected_agents", [])
        completed_tasks = state.get("completed_tasks", [])
        failed_tasks = state.get("failed_tasks", [])

        results = []

        if plan and plan.tasks:
            for task in plan.tasks:
                use_collaboration = state.get("use_collaboration", False)
                res = self.agent_router.route_and_execute(
                    task, state, use_collaboration=use_collaboration
                )
                agent = res.get("agent_used")

                if agent and agent not in selected_agents:
                    selected_agents.append(agent)

                if task.status == "COMPLETED":
                    completed_tasks.append(task.task_id)
                else:
                    failed_tasks.append(task.task_id)

                results.append(res)

        elapsed_ms = (time.time() - start_time) * 1000

        # We store task results transiently to use in merge_results
        return {
            "selected_agents": selected_agents,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed_ms,
            "task_results": results,
        }

    def merge_results(self, state: SupervisorState) -> dict:
        """
        Combines results from various agents and produces the final response.
        """
        start_time = time.time()
        temp_results = state.get("task_results", [])

        if not temp_results:
            final_response = "No tasks were executed."
        elif len(temp_results) == 1:
            final_response = temp_results[0].get("result", "")
        else:
            # Simple concatenation for now; in a full implementation, the LLM could summarize them.
            final_response = "\n\n".join(
                [
                    f"### Task Result from {r.get('agent_used')}:\n{r.get('result')}"
                    for r in temp_results
                ]
            )

        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "final_response": final_response,
            "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed_ms,
        }

    def run(self, initial_state: SupervisorState) -> dict:
        """
        Executes the Supervisor Graph and returns the final state.
        """
        logger.info("Starting Supervisor Graph execution...")
        final_state = self.graph.invoke(initial_state)
        logger.info(
            f"Supervisor Graph completed in {final_state.get('execution_time_ms', 0):.2f}ms"
        )
        return final_state
