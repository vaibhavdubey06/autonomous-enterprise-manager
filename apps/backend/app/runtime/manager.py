import logging
from typing import Dict, Optional
from app.runtime.models import RuntimeSession
from app.runtime.engine import EnterpriseRuntime
from app.agents.supervisor.supervisor_agent import SupervisorGraph

logger = logging.getLogger(__name__)


class RuntimeManager:
    """
    Manages multiple active RuntimeSessions and their respective EnterpriseRuntime instances.
    Aligns with multi-user, multi-tenant enterprise deployments.
    """

    def __init__(self):
        self._runtimes: Dict[str, EnterpriseRuntime] = {}

    def create_session(
        self,
        user_session_id: str,
        conversation_id: str,
        supervisor_graph: SupervisorGraph,
    ) -> EnterpriseRuntime:
        """
        Creates a new RuntimeSession and wires it to an EnterpriseRuntime.
        """
        session = RuntimeSession(
            user_session_id=user_session_id, conversation_id=conversation_id
        )
        runtime = EnterpriseRuntime(session, supervisor_graph)
        self._runtimes[session.session_id] = runtime

        logger.info(
            f"Created RuntimeSession {session.session_id} for conversation {conversation_id}"
        )

        # Emit creation telemetry
        span = runtime.trace_manager.start_span(
            trace_id=conversation_id,
            operation="runtime_created",
            session_id=session.session_id,
        )
        runtime.trace_manager.end_span(span, "OK")

        return runtime

    def get_runtime(self, session_id: str) -> Optional[EnterpriseRuntime]:
        return self._runtimes.get(session_id)

    def cleanup_session(self, session_id: str):
        if session_id in self._runtimes:
            logger.info(f"Cleaning up RuntimeSession {session_id}")
            del self._runtimes[session_id]


runtime_manager = RuntimeManager()
