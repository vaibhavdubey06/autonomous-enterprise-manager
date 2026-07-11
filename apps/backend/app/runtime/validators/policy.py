import logging
from typing import Optional, Dict, Any

from app.runtime.validators.base import (
    PreExecutionValidator,
    ValidationResult,
    ValidationAction,
)

logger = logging.getLogger(__name__)


class PolicyValidator(PreExecutionValidator):
    """
    Stub validator for enterprise policy checks.

    Future responsibilities:
    - Maintenance mode / feature flags
    - Tenant policy enforcement
    - Rate limiting
    - Quota validation
    - Authentication / authorization checks
    - Request normalization

    Currently always allows requests through.
    """

    @property
    def name(self) -> str:
        return "policy_validation"

    def validate(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        # Stub: always allow. Extend with real policy checks as needed.
        return ValidationResult(
            action=ValidationAction.ALLOW,
            validator_name=self.name,
        )
