import logging
from typing import List, Optional, Dict, Any

from app.operations.tracing.trace_manager import TraceManager
from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.guardrails.base import BaseDetector
from app.services.llm.guardrails.models import (
    GuardrailFinding,
    GuardrailResult,
    PolicyAction,
)
from app.services.llm.guardrails.policy import GuardrailPolicy

logger = logging.getLogger(__name__)


class GuardrailEngine:
    """
    Executes loaded detectors, aggregates findings, and applies policies.
    """

    def __init__(
        self, detectors: List[BaseDetector], policy: Optional[GuardrailPolicy] = None
    ):
        self.detectors = detectors
        self.policy = policy or GuardrailPolicy()
        self.trace_manager = TraceManager()

    def evaluate_request(
        self, request: LLMRequest, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Run all detectors that apply to the request phase."""
        applicable_detectors = [d for d in self.detectors if d.applies_to_request]
        return self._run_evaluation(applicable_detectors, request, None, context)

    def evaluate_response(
        self,
        request: LLMRequest,
        response: LLMResponse,
        context: Optional[Dict[str, Any]] = None,
    ) -> GuardrailResult:
        """Run all detectors that apply to the response phase."""
        applicable_detectors = [d for d in self.detectors if d.applies_to_response]
        return self._run_evaluation(applicable_detectors, request, response, context)

    def _run_evaluation(
        self,
        detectors: List[BaseDetector],
        request: LLMRequest,
        response: Optional[LLMResponse],
        context: Optional[Dict[str, Any]],
    ) -> GuardrailResult:
        all_findings: List[GuardrailFinding] = []
        final_action = PolicyAction.ALLOW
        total_risk = 0.0

        for detector in detectors:
            # Emit telemetry for each detector execution
            with self.trace_manager.trace(
                "guardrail_evaluation", detector=detector.name
            ) as span:
                try:
                    findings = detector.analyze(request, response, context)

                    for finding in findings:
                        # Apply policy to finding
                        policy_action = self.policy.get_action(finding.detector_name)
                        finding.action = policy_action

                        span.attributes["finding"] = finding.message
                        span.attributes["severity"] = finding.severity.value
                        span.attributes["action"] = policy_action.value

                        all_findings.append(finding)
                        total_risk += finding.score

                        # Escalate final action if needed (BLOCK > WARN > ALLOW)
                        if policy_action == PolicyAction.BLOCK:
                            final_action = PolicyAction.BLOCK
                        elif (
                            policy_action == PolicyAction.WARN
                            and final_action != PolicyAction.BLOCK
                        ):
                            final_action = PolicyAction.WARN

                except Exception as e:
                    logger.error(f"Detector {detector.name} failed: {e}")
                    span.attributes["error"] = str(e)

        return GuardrailResult(
            action=final_action,
            findings=all_findings,
            risk_score=total_risk,
            metadata={"detectors_run": [d.name for d in detectors]},
        )
