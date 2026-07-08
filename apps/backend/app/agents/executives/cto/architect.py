import logging
from typing import List
from pydantic import BaseModel
from app.services.llm.gateway import LLMGateway
from app.agents.executives.cto.prompts import CTO_ARCHITECT_PROMPT

logger = logging.getLogger(__name__)


class ArchitectureFindings(BaseModel):
    scalability_score: int
    modularity_score: int
    maintainability_score: int
    findings: List[str]
    recommendations: List[str]


class ArchitectureReviewer:
    """
    Evaluates technical context for architectural properties like scalability and cohesion.
    """

    def __init__(self, llm_service: LLMGateway):
        self.llm_service = llm_service

    def review(self, objective: str, context: str) -> ArchitectureFindings:
        prompt = CTO_ARCHITECT_PROMPT.format(objective=objective, context=context)
        logger.info("ArchitectureReviewer analyzing context...")

        try:
            json_str = self.llm_service.generate_structured(
                prompt, ArchitectureFindings
            )
            import json

            return ArchitectureFindings(**json.loads(json_str))
        except Exception as e:
            logger.error(f"ArchitectureReviewer failed: {e}")
            return ArchitectureFindings(
                scalability_score=0,
                modularity_score=0,
                maintainability_score=0,
                findings=["Error occurred during architectural review."],
                recommendations=["Manual review required."],
            )
