from pydantic import BaseModel
from typing import Optional
from contextvars import ContextVar
from .identity_models import Identity


class SecurityContext(BaseModel):
    identity: Optional[Identity] = None
    session_id: Optional[str] = None
    api_key_id: Optional[str] = None
    trace_id: Optional[str] = None
    request_ip: Optional[str] = None


# Context variables for dependency injection / background tasks
_security_context_var: ContextVar[Optional[SecurityContext]] = ContextVar(
    "security_context", default=None
)


def set_security_context(context: SecurityContext) -> None:
    _security_context_var.set(context)


def get_security_context() -> Optional[SecurityContext]:
    return _security_context_var.get()


def get_current_identity() -> Optional[Identity]:
    ctx = get_security_context()
    return ctx.identity if ctx else None
