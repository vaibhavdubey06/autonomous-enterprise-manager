from app.capabilities.base.executor import CapabilityExecutor
from app.capabilities.base.schemas import CapabilityResult
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from app.services.llm.llm_service import LLMService
from app.agents.base.profile import AgentProfile
from app.agents.base.task import ExecutiveTask
from app.agents.base.output import ExecutiveResult
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseExecutiveAgent(ABC):
    """
    Abstract Base Class for all Executive Agents (CTO, CFO, COO, etc.).
    Provides reusable functionality for retrieval, reasoning, and structured output.
    """

    def __init__(
        self,
        llm_service: LLMService,
        capability_executor: Optional[CapabilityExecutor] = None,
    ):
        self.llm_service = llm_service
        self.capability_executor = capability_executor

    @abstractmethod
    def get_profile(self) -> AgentProfile:
        """
        Returns the profile metadata for the agent.
        """
        pass

    @abstractmethod
    def execute(self, task: ExecutiveTask, state: Dict[str, Any]) -> ExecutiveResult:
        """
        Executes the assigned task and returns a standardized ExecutiveResult.
        Must be implemented by the specific Executive Agent.
        """
        pass

    def retrieve_enterprise_knowledge(
        self, query: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Legacy method for direct RAG retrieval. Preserved for backward compatibility.
        """
        # If knowledge agent was not passed in via kwargs (since we removed it from init)
        # we will log a warning and return empty.
        logger.warning(
            "retrieve_enterprise_knowledge is deprecated. Use capabilities instead."
        )
        return {"answer": "Legacy retrieval unavailable.", "sources": []}

    def invoke_capability(
        self, capability_id: str, action: str, **kwargs
    ) -> CapabilityResult:
        """
        Delegates to the Capability Executor to run tools, workflows, or APIs.
        """
        if not self.capability_executor:
            logger.warning(
                "Capability Executor is not injected. Skipping capability invocation."
            )
            from app.capabilities.base.schemas import CapabilityResult

            return CapabilityResult(
                success=False,
                capability_name=capability_id,
                action=action,
                status="FAILED",
                errors=["Capability Executor not available."],
            )

        logger.info(
            f"[{self.get_profile().agent_name}] Invoking capability {capability_id}.{action}"
        )
        return self.capability_executor.execute(
            agent_name=self.get_profile().agent_name,
            capability_id=capability_id,
            action=action,
            **kwargs,
        )

    def reason(self, prompt: str) -> str:
        """
        Uses Gemini to reason about a problem or generate unstructured text.
        """
        logger.info(f"[{self.get_profile().agent_name}] Reasoning...")
        # A simple unstructured query to the LLM (bypassing strict RAG context if needed for reasoning)
        # However, our LLMService currently enforces strict RAG in `generate_answer`.
        # For general reasoning, we should use the base model.
        # But wait, LLMService has generate_structured now. We can also add a generate_unstructured.
        # For now, we will use generate_structured if we want structured, or we can add a simple generate_text.
        # Let's rely on generate_structured primarily as requested by the framework.
        raise NotImplementedError("Use reason_structured for typed outputs.")

    def reason_structured(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        """
        Uses Gemini to generate structured output conforming to a Pydantic schema.
        """
        logger.info(
            f"[{self.get_profile().agent_name}] Generating structured reasoning for schema {schema.__name__}"
        )
        json_str = self.llm_service.generate_structured(prompt, schema)
        import json

        return schema(**json.loads(json_str))

    def _create_result(
        self,
        task: ExecutiveTask,
        summary: str,
        reasoning: str,
        recommendations: List[str],
        sources: List[Dict[str, Any]],
        metrics: Optional[Dict[str, Any]] = None,
    ) -> ExecutiveResult:
        """
        Helper method to construct the standardized ExecutiveResult.
        """
        return ExecutiveResult(
            task_id=task.task_id,
            agent=self.get_profile().agent_name,
            summary=summary,
            reasoning=reasoning,
            recommendations=recommendations,
            confidence=0.9,  # Default, can be overridden by specific agents
            sources=sources,
            artifacts=[],
            execution_metrics=metrics or {},
        )
