import json
import logging
from typing import Optional
from app.agents.supervisor.schemas import ExecutionPlan
from app.services.llm.gateway import LLMGateway
from app.services.decisions.engine import DecisionEngine
from app.services.decisions.models import DecisionType
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AdaptedTemplateResponse(BaseModel):
    autonomy_level: int
    milestones: list[str]
    modified_tasks: list[dict]  # Just tracking modifications for simplicity


class WorkflowTemplateEngine:
    """
    Standalone engine responsible for dynamically adapting declarative workflow templates
    based on real-time goals and context.
    """

    def __init__(self, llm_service: LLMGateway, decision_engine: DecisionEngine):
        self.llm_service = llm_service
        self.decision_engine = decision_engine

    def adapt_template(
        self,
        plan: ExecutionPlan,
        goal: str,
        context: str,
        trace_id: Optional[str] = None,
    ) -> ExecutionPlan:
        """
        Dynamically adapts a loaded workflow template before execution.
        """
        logger.info(f"Adapting template '{plan.workflow_template}' for goal: {goal}")

        prompt = (
            f"You are the Enterprise Workflow Engine.\n"
            f"Adapt the following workflow template for the specific goal.\n"
            f"Goal: {goal}\n"
            f"Context: {context}\n"
            f"Template Original Milestones: {plan.milestones}\n"
            f"Return the necessary autonomy level, updated milestones, and any task overrides."
        )

        try:
            # We use structured generation to get the adaptation
            json_response = self.llm_service.generate_structured(
                prompt, AdaptedTemplateResponse
            )

            cleaned = json_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            data = json.loads(cleaned.strip())
            adaptation = AdaptedTemplateResponse(**data)

            # Apply adaptation
            plan.autonomy_level = adaptation.autonomy_level
            plan.milestones = adaptation.milestones
            # In a full implementation, we'd apply task overrides here

            # Record governance decision
            self.decision_engine.record_decision(
                decision_type=DecisionType.PLANNING,
                component="WorkflowTemplateEngine",
                selected_option="LLM_Adapted_Template",
                context={
                    "original_template": plan.workflow_template,
                    "new_autonomy_level": plan.autonomy_level,
                },
                trace_id=trace_id,
            )

            return plan

        except Exception as e:
            logger.error(
                f"Template adaptation failed, falling back to static template: {e}"
            )
            return plan
