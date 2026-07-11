import logging
from typing import List, Optional, Dict, Any

from app.operations.tracing.trace_manager import TraceManager
from app.operations.telemetry.telemetry_context import TelemetryContext
from app.runtime.validators.base import (
    PreExecutionValidator,
    ValidationResult,
    ValidationAction,
)

logger = logging.getLogger(__name__)


class PreExecutionResult:
    """Aggregated result from the full pre-execution pipeline."""

    def __init__(self):
        self.allowed: bool = True
        self.rejection_message: str = ""
        self.rejected_by: str = ""
        self.validator_results: List[ValidationResult] = []

    def reject(self, result: ValidationResult):
        self.allowed = False
        self.rejection_message = result.message
        self.rejected_by = result.validator_name
        self.validator_results.append(result)

    def allow(self, result: ValidationResult):
        self.validator_results.append(result)


class PreExecutionPipeline:
    """
    Reusable pre-execution pipeline that runs inside EnterpriseRuntime.start()
    before the SupervisorGraph begins.

    Guarantees that every execution path (FastAPI, Streamlit, MCP, A2A, CLI,
    scheduled workflows, future SDKs) shares exactly the same validation logic.

    Pipeline stages:
    1. Domain Validation   — is the request within the enterprise domain?
    2. Policy Validation   — maintenance mode, feature flags, tenant policies
    (extensible: add more validators as needed)
    """

    def __init__(self, validators: Optional[List[PreExecutionValidator]] = None):
        if validators is not None:
            self.validators = validators
        else:
            # Default pipeline
            from app.runtime.validators.domain import DomainValidator
            from app.runtime.validators.policy import PolicyValidator

            self.validators = [
                DomainValidator(),
                PolicyValidator(),
            ]

        self.trace_manager = TraceManager()

    def execute(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> PreExecutionResult:
        """
        Run all validators sequentially. Short-circuit on the first REJECT.

        Args:
            user_input: The raw user question (no system prompt wrappers).
            context: Optional metadata (session_id, user_id, tenant, etc.).

        Returns:
            PreExecutionResult with allowed=True or rejection details.
        """
        pipeline_result = PreExecutionResult()

        telemetry_snap = TelemetryContext.get_snapshot()
        trace_id = telemetry_snap.get("trace_id")

        # Top-level pre_execution span
        pre_exec_span = self.trace_manager.start_span(
            trace_id=trace_id or "pre_exec",
            operation="pre_execution",
            parent_span_id=telemetry_snap.get("span_id"),
            validator_count=len(self.validators),
        )

        try:
            for validator in self.validators:
                # Per-validator telemetry span
                validator_span = self.trace_manager.start_span(
                    trace_id=pre_exec_span.trace_id,
                    operation=validator.name,
                    parent_span_id=pre_exec_span.span_id,
                )

                try:
                    result = validator.validate(user_input, context)

                    validator_span.attributes["action"] = result.action.value
                    if result.metadata:
                        validator_span.attributes["metadata"] = str(result.metadata)

                    if result.action == ValidationAction.REJECT:
                        pipeline_result.reject(result)

                        # Emit rejection telemetry
                        reject_span = self.trace_manager.start_span(
                            trace_id=pre_exec_span.trace_id,
                            operation="request_rejected",
                            parent_span_id=pre_exec_span.span_id,
                            rejected_by=validator.name,
                            message=result.message[:200],
                        )
                        self.trace_manager.end_span(reject_span, "OK")

                        self.trace_manager.end_span(validator_span, "OK")

                        logger.info(
                            "PreExecution rejected by %s: %s",
                            validator.name,
                            result.message[:100],
                        )
                        break  # Short-circuit
                    else:
                        pipeline_result.allow(result)
                        self.trace_manager.end_span(validator_span, "OK")

                except Exception as e:
                    logger.error("Validator %s raised exception: %s", validator.name, e)
                    validator_span.attributes["error"] = str(e)
                    self.trace_manager.end_span(validator_span, "ERROR")
                    # Fail-open: continue to next validator

            self.trace_manager.end_span(
                pre_exec_span,
                "OK" if pipeline_result.allowed else "REJECTED",
            )

        except Exception as e:
            logger.error("PreExecutionPipeline failed: %s", e)
            pre_exec_span.attributes["error"] = str(e)
            self.trace_manager.end_span(pre_exec_span, "ERROR")
            # Fail-open on pipeline-level errors

        return pipeline_result
