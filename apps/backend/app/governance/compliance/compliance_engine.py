from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.governance.context.governance_context import GovernanceContext


class BaseComplianceDetector(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def detect(self, context: GovernanceContext) -> Dict[str, Any]:
        """Returns dict with 'detected': bool, 'details': str"""
        pass


class PIIDetector(BaseComplianceDetector):
    @property
    def name(self) -> str:
        return "PII Detector"

    def detect(self, context: GovernanceContext) -> Dict[str, Any]:
        target = f"{context.workflow_goal} {context.task_description or ''}".lower()
        pii_keywords = ["ssn", "social security", "credit card", "passport"]
        for kw in pii_keywords:
            if kw in target:
                return {"detected": True, "details": f"Found potential PII: {kw}"}
        return {"detected": False, "details": ""}


class ConfidentialDetector(BaseComplianceDetector):
    @property
    def name(self) -> str:
        return "Confidential Data Detector"

    def detect(self, context: GovernanceContext) -> Dict[str, Any]:
        target = f"{context.workflow_goal} {context.task_description or ''}".lower()
        confidential_keywords = [
            "internal only",
            "confidential",
            "secret",
            "proprietary",
        ]
        for kw in confidential_keywords:
            if kw in target:
                return {"detected": True, "details": f"Found confidential marker: {kw}"}
        return {"detected": False, "details": ""}


class ComplianceEngine:
    def __init__(self):
        self.detectors: List[BaseComplianceDetector] = [
            PIIDetector(),
            ConfidentialDetector(),
        ]

    def register_detector(self, detector: BaseComplianceDetector):
        self.detectors.append(detector)

    def run_compliance_checks(self, context: GovernanceContext) -> List[Dict[str, Any]]:
        results = []
        for detector in self.detectors:
            res = detector.detect(context)
            if res.get("detected"):
                results.append(
                    {"detector": detector.name, "details": res.get("details")}
                )
        return results
