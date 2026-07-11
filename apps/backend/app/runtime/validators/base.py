import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ValidationAction(str, Enum):
    ALLOW = "ALLOW"
    REJECT = "REJECT"


class ValidationResult(BaseModel):
    """Result of a single pre-execution validator."""

    action: ValidationAction = ValidationAction.ALLOW
    validator_name: str = ""
    message: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PreExecutionValidator(ABC):
    """
    Abstract base class for all pre-execution validators.
    Each validator inspects the raw user input before the SupervisorGraph runs.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this validator, used in telemetry and logging."""
        ...

    @abstractmethod
    def validate(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate the raw user input.

        Args:
            user_input: The original user question/prompt (no system wrappers).
            context: Optional metadata (session_id, user_id, tenant, etc.).

        Returns:
            ValidationResult indicating ALLOW or REJECT.
        """
        ...
