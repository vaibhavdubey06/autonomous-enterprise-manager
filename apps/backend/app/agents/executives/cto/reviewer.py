import logging
from typing import List
from pydantic import BaseModel
from app.services.llm.llm_service import LLMService
from app.agents.executives.cto.prompts import CTO_REVIEWER_PROMPT

logger = logging.getLogger(__name__)

class ReviewFindings(BaseModel):
    tech_debt_issues: List[str]
    documentation_gaps: List[str]
    best_practice_violations: List[str]
    recommendations: List[str]

class TechnicalReviewer:
    """
    Reviews technical context, architecture, or design decisions for technical debt, 
    documentation gaps, and best practices.
    """
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def review(self, objective: str, context: str) -> ReviewFindings:
        prompt = CTO_REVIEWER_PROMPT.format(
            objective=objective,
            context=context
        )
        logger.info("TechnicalReviewer analyzing context...")
        
        try:
            json_str = self.llm_service.generate_structured(prompt, ReviewFindings)
            import json
            return ReviewFindings(**json.loads(json_str))
        except Exception as e:
            logger.error(f"TechnicalReviewer failed: {e}")
            return ReviewFindings(
                tech_debt_issues=["Error occurred during technical review."],
                documentation_gaps=[],
                best_practice_violations=[],
                recommendations=["Manual review required."]
            )
