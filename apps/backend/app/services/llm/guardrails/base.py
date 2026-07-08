from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict

from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.guardrails.models import GuardrailFinding


class BaseDetector(ABC):
    """
    Abstract interface for all Guardrail Detectors.
    Detectors analyze requests or responses and yield findings.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the detector (e.g. 'prompt_injection')"""
        pass

    @property
    def applies_to_request(self) -> bool:
        """Whether this detector should run before the LLM is called."""
        return True
        
    @property
    def applies_to_response(self) -> bool:
        """Whether this detector should run after the LLM has responded."""
        return False

    @abstractmethod
    def analyze(self, request: LLMRequest, response: Optional[LLMResponse] = None, context: Optional[Dict[str, Any]] = None) -> List[GuardrailFinding]:
        """
        Analyze the incoming request or outgoing response.
        If analyzing the request, `response` will be None.
        Returns a list of GuardrailFinding objects for anything detected.
        """
        pass
