import logging
from typing import Any
from app.agents.supervisor.schemas import Task, TaskStatus
from app.agents.base.registry import AgentRegistry
from app.agents.base.capabilities import Capability
from app.agents.base.task import ExecutiveTask

logger = logging.getLogger(__name__)


class AgentRouter:
    """
    Routes a Task to the appropriate specialist agent for execution via the AgentRegistry.
    Falls back to the Knowledge Agent for direct retrieval tasks if no executive is assigned.
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        knowledge_agent_graph=None,
        collaboration_manager=None,
    ):
        self.agent_registry = agent_registry
        self.knowledge_agent = knowledge_agent_graph
        self.collaboration_manager = collaboration_manager

    def _capability_name(self, capability: Any) -> str:
        if isinstance(capability, Capability):
            return capability.value
        return str(capability)

    def _resolve_agent_name(self, task: Task) -> str:
        required_capabilities = {
            self._capability_name(capability)
            for capability in task.required_capabilities
            if capability
        }

        if required_capabilities:
            best_agent_name = None
            best_score = 0

            for profile in self.agent_registry.list_agents():
                profile_capabilities = {
                    self._capability_name(capability)
                    for capability in profile.capabilities
                }
                score = len(required_capabilities & profile_capabilities)
                if score > best_score:
                    best_score = score
                    best_agent_name = profile.agent_name

            if best_agent_name and best_score > 0:
                return best_agent_name

        return task.assigned_agent or "Knowledge Agent"

    def route_and_execute(
        self, task: Task, state: dict, use_collaboration: bool = False
    ) -> dict:
        """
        Selects the appropriate agent, executes the task, and returns the result.
        """
        from app.operations.tracing.trace_manager import TraceManager
        from app.operations.telemetry.telemetry_context import TelemetryContext

        agent_name = self._resolve_agent_name(task)
        logger.info(f"Routing task {task.task_id} to {agent_name}")

        telemetry_snap = TelemetryContext.get_snapshot()
        trace_id = telemetry_snap.get("trace_id")
        trace_manager = TraceManager()

        if not trace_id:
            span = trace_manager.start_trace("agent_routing")
        else:
            span = trace_manager.start_span(
                trace_id=trace_id,
                operation="agent_routing",
                parent_span_id=telemetry_snap.get("span_id"),
                expected_capability=(
                    ",".join(str(c) for c in task.required_capabilities)
                    if task.required_capabilities
                    else "general"
                ),
                detected_capability=(
                    ",".join(str(c) for c in task.required_capabilities)
                    if task.required_capabilities
                    else "general"
                ),
                selected_agent=agent_name,
            )

        try:
            result = self._execute_routed_task(
                task, state, agent_name, use_collaboration
            )
            trace_manager.end_span(span, "OK")
            return result
        except Exception as e:
            span.attributes["error"] = str(e)
            trace_manager.end_span(span, "ERROR")
            raise

    def _execute_routed_task(
        self, task: Task, state: dict, agent_name: str, use_collaboration: bool
    ) -> dict:
        # Branch for Collaboration Runtime
        if use_collaboration and self.collaboration_manager:
            logger.info(f"Executing task {task.task_id} via Collaboration Runtime")
            session = self.collaboration_manager.create_session(
                objective=task.description
            )
            self.collaboration_manager.form_team(session.session_id)
            self.collaboration_manager.execute(session.session_id)

            # Simulate work for POC by just delegating the main task
            delegated = self.collaboration_manager.delegation.delegate_task(
                task.description, agent_name
            )
            self.collaboration_manager.delegation.complete_task(delegated.task_id)

            # Fire and forget the async complete_session to avoid event loop conflicts
            import threading
            import asyncio

            def _complete_session_in_thread(sid: str):
                from app.core.database import SessionLocal
                from app.collaboration.coordinator.collaboration_manager import CollaborationManager
                db = SessionLocal()
                try:
                    manager = CollaborationManager(
                        db,
                        self.collaboration_manager.team_builder.registry,
                        self.collaboration_manager.governance_pipeline
                    )
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        manager.complete_session(sid)
                    )
                    loop.close()
                except Exception as e:
                    logger.error(f"Failed to complete session: {e}")
                finally:
                    db.close()

            threading.Thread(target=_complete_session_in_thread, args=(session.session_id,), daemon=True).start()

            task.status = TaskStatus.COMPLETED
            return {
                "task_id": task.task_id,
                "agent_used": agent_name,
                "result": f"Executed via Collaboration Session {session.session_id} - Task: {delegated.description}",
                "sources": [],
                "metrics": {},
            }

        # Try to find a registered Executive Agent
        executive = self.agent_registry.get_agent(agent_name)

        if executive:
            # Map Supervisor Task to Executive Task
            exec_task = ExecutiveTask(
                task_id=task.task_id,
                goal=task.goal,
                description=task.description,
                priority=task.priority,
                dependencies=task.dependencies,
                assigned_agent=agent_name,
                required_capabilities=task.required_capabilities,
                context=task.context,
                artifacts=task.artifacts,
            )

            try:
                result = executive.execute(exec_task, state)
                task.status = TaskStatus.COMPLETED
                return {
                    "task_id": task.task_id,
                    "agent_used": agent_name,
                    "result": result.reasoning + "\n\n" + result.summary,
                    "sources": result.sources,
                    "metrics": result.execution_metrics,
                }
            except Exception as e:
                logger.error(f"Executive Agent {agent_name} failed: {e}")
                task.status = TaskStatus.FAILED
                return {
                    "task_id": task.task_id,
                    "agent_used": agent_name,
                    "result": f"Execution failed: {str(e)}",
                    "sources": [],
                    "metrics": {},
                }

        # Fallback for placeholders or direct Knowledge Agent calls
        if agent_name != "Knowledge Agent":
            logger.warning(
                f"{agent_name} not found in registry or is a placeholder. Routing to Knowledge Agent."
            )
            agent_name = "Knowledge Agent"

        # Execute using Knowledge Agent (existing RAG LangGraph)
        if self.knowledge_agent:
            logger.info("Executing task via Knowledge Agent graph.")
            sub_state: dict[str, Any] = {
                "question": task.description,
                "session_id": state.get("session_id"),
                "conversation_id": state.get("conversation_id"),
                "execution_trace": [],
                "metrics": {},
                "tool_results": [],
                "sources": [],
                "reranked_chunks": [],
                "semantic_memory": [],
                "recent_memory": [],
            }

            result_state = self.knowledge_agent.run(sub_state)
            task.status = TaskStatus.COMPLETED

            return {
                "task_id": task.task_id,
                "agent_used": "Knowledge Agent",
                "result": result_state.get("answer", ""),
                "sources": result_state.get("sources", []),
                "metrics": result_state.get("metrics", {}),
            }

        else:
            logger.error("Knowledge Agent graph not provided to Router.")
            task.status = TaskStatus.FAILED
            return {
                "task_id": task.task_id,
                "agent_used": "None",
                "result": "Execution failed: No agent available to process this task.",
                "sources": [],
                "metrics": {},
            }
