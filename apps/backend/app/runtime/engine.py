import logging
import time
import asyncio
from typing import Dict, Any, Optional
from app.runtime.models import RuntimeState, RuntimeSession
from app.agents.supervisor.supervisor_agent import SupervisorGraph
from app.agents.supervisor.schemas import SupervisorState
from app.operations.tracing.trace_manager import TraceManager

logger = logging.getLogger(__name__)


class EnterpriseRuntime:
    """
    Manages a single RuntimeSession. Encapsulates SupervisorGraph to
    handle start, pause, resume, cancel, checkpoint, restore workflows.
    Emits deep telemetry.
    """

    def __init__(self, session: RuntimeSession, supervisor_graph: SupervisorGraph):
        self.session = session
        self.supervisor_graph = supervisor_graph
        self.trace_manager = TraceManager()
        self._pause_requested = False

    async def _emit_telemetry(self, operation: str, **kwargs):
        span = self.trace_manager.start_span(
            trace_id=self.session.conversation_id,
            operation=operation,
            session_id=self.session.session_id,
            state=self.session.state.value,
            **kwargs,
        )
        self.trace_manager.end_span(span, "OK")

    def _update_state(self, new_state: RuntimeState):
        self.session.state = new_state
        # We can run emit telemetry synchronously via trace_manager
        span = self.trace_manager.start_span(
            trace_id=self.session.conversation_id,
            operation=f"runtime_{new_state.value.lower()}",
            session_id=self.session.session_id,
        )
        self.trace_manager.end_span(span, "OK")

    async def start(self, user_input: str) -> Dict[str, Any]:
        self._update_state(RuntimeState.INITIALIZED)

        initial_state: SupervisorState = {
            "user_input": user_input,
            "session_id": self.session.user_session_id,
            "conversation_id": self.session.conversation_id,
            "memory_context": "",
            "execution_time_ms": 0.0,
            "selected_agents": [],
            "completed_tasks": [],
            "failed_tasks": [],
        }

        start_time = time.time()
        self._update_state(RuntimeState.EXECUTING)

        try:
            # For simplicity, we just invoke LangGraph entirely.
            # In a highly distributed setup, this would yield between nodes.
            final_state = await self.supervisor_graph.run(initial_state)

            # Sync back some session details
            self.session.active_agents = list(
                set(self.session.active_agents + final_state.get("selected_agents", []))
            )

            if final_state.get("workflow_state") == "FAILED":
                self._update_state(RuntimeState.FAILED)
            else:
                self._update_state(RuntimeState.COMPLETED)

            duration = (time.time() - start_time) * 1000

            # Emit finish telemetry
            span = self.trace_manager.start_span(
                trace_id=self.session.conversation_id,
                operation="runtime_duration",
                duration_ms=duration,
            )
            self.trace_manager.end_span(span, "OK")

            return final_state
        except asyncio.CancelledError:
            self._update_state(RuntimeState.CANCELLED)
            raise
        except Exception as e:
            logger.error(f"Runtime failed: {e}")
            self._update_state(RuntimeState.FAILED)
            span = self.trace_manager.start_span(
                trace_id=self.session.conversation_id,
                operation="runtime_failed",
                error=str(e),
            )
            self.trace_manager.end_span(span, "ERROR")
            raise

    async def pause(self):
        self._pause_requested = True
        self._update_state(RuntimeState.PAUSED)

    async def resume(self):
        self._pause_requested = False
        self._update_state(RuntimeState.EXECUTING)
        # Resuming LangGraph requires passing thread_id to ainvoke, which is handled
        # internally if we supported yielding. Since this is an MVP of the Runtime,
        # we mark state.

    async def cancel(self):
        self._update_state(RuntimeState.CANCELLED)

    async def checkpoint(self):
        # Triggering checkpoint event for telemetry
        await self._emit_telemetry("runtime_checkpoint")

    async def restore(self):
        await self._emit_telemetry("runtime_restored")

    async def replay(self):
        await self._emit_telemetry("runtime_replayed")

    def status(self) -> dict:
        return self.session.dict()
