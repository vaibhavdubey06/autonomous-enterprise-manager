import contextvars
from typing import Optional


class TelemetryContext:
    """Thread-safe telemetry context using contextvars for async propagation."""

    _trace_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "trace_id", default=None
    )
    _span_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "span_id", default=None
    )
    _request_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "request_id", default=None
    )
    _session_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "session_id", default=None
    )
    _conversation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "conversation_id", default=None
    )
    _workflow_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "workflow_id", default=None
    )
    _collaboration_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "collaboration_id", default=None
    )
    _governance_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "governance_id", default=None
    )
    _executive_agent: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "executive_agent", default=None
    )
    _capability: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "capability", default=None
    )
    _user: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "user", default=None
    )
    _model: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "model", default=None
    )
    _correlation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "correlation_id", default=None
    )

    @classmethod
    def new_context(cls, **kwargs) -> dict:
        """Set a new telemetry context. Returns the previous values for restoration."""
        tokens = {}
        for key, value in kwargs.items():
            var = getattr(cls, f"_{key}", None)
            if var and isinstance(var, contextvars.ContextVar):
                tokens[key] = var.set(value)
        return tokens

    @classmethod
    def get_snapshot(cls) -> dict:
        """Capture the current context as a plain dict."""
        return {
            "trace_id": cls._trace_id.get(),
            "span_id": cls._span_id.get(),
            "request_id": cls._request_id.get(),
            "session_id": cls._session_id.get(),
            "conversation_id": cls._conversation_id.get(),
            "workflow_id": cls._workflow_id.get(),
            "collaboration_id": cls._collaboration_id.get(),
            "governance_id": cls._governance_id.get(),
            "executive_agent": cls._executive_agent.get(),
            "capability": cls._capability.get(),
            "user": cls._user.get(),
            "model": cls._model.get(),
            "correlation_id": cls._correlation_id.get(),
        }

    @classmethod
    def reset(cls):
        """Reset all context variables to None."""
        for attr_name in dir(cls):
            if attr_name.startswith("_") and not attr_name.startswith("__"):
                var = getattr(cls, attr_name)
                if isinstance(var, contextvars.ContextVar):
                    var.set(None)
