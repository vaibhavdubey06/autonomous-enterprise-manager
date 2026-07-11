import logging
from typing import Optional, Dict, Any

from app.runtime.validators.base import (
    PreExecutionValidator,
    ValidationResult,
    ValidationAction,
)
from app.services.llm.models import LLMRequest, LLMConfig

logger = logging.getLogger(__name__)


class DomainValidator(PreExecutionValidator):
    """
    Validates that the user's query falls within the accepted domain of the
    Autonomous Enterprise Manager.

    Uses OpenRouter's free model for fast, low-cost classification.
    Operates on the **raw** user input — no system prompt wrappers — so the
    classifier cannot be tricked by internal system instructions.
    """

    CLASSIFICATION_PROMPT = (
        "You are a strict domain classifier. Determine if the following user query "
        "is within the accepted domain of an Autonomous Enterprise Manager.\n\n"
        "ACCEPTED DOMAIN:\n"
        "- Enterprise AI Operations\n"
        "- Software Engineering, Code Analysis, Architecture\n"
        "- GitHub Repositories, Pull Requests, Issues, Commits\n"
        "- Internal company documentation and knowledge base (RAG)\n"
        "- DevOps, CI/CD, Infrastructure\n"
        "- Project management and workflow automation\n"
        "- General greetings or clarifications about the agent's capabilities\n\n"
        "OUT OF DOMAIN (reject):\n"
        "- General knowledge questions (capitals, history, science trivia)\n"
        "- Cooking recipes, sports scores, entertainment\n"
        "- Medical, legal, or financial advice\n"
        "- Any topic unrelated to enterprise software operations\n\n"
        "Respond with EXACTLY one word: YES if the query is OUT OF DOMAIN, "
        "or NO if it is within the accepted domain."
    )

    @property
    def name(self) -> str:
        return "domain_validation"

    def validate(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        try:
            from app.services.llm.providers.openrouter import OpenRouterProvider

            provider = OpenRouterProvider()

            eval_request = LLMRequest(
                prompt=f"{self.CLASSIFICATION_PROMPT}\n\nUser Query: {user_input}",
                config=LLMConfig(temperature=0.0, max_output_tokens=10),
            )

            response = provider.generate(eval_request)
            answer = response.content.strip().upper()

            if "YES" in answer:
                logger.info(
                    "DomainValidator rejected query as out-of-domain: %s",
                    user_input[:80],
                )
                return ValidationResult(
                    action=ValidationAction.REJECT,
                    validator_name=self.name,
                    message=(
                        "Your question appears to be outside my area of expertise. "
                        "I'm designed to help with enterprise software operations, "
                        "code analysis, GitHub repositories, and internal documentation. "
                        "Please ask a question related to these topics."
                    ),
                    metadata={"raw_answer": answer, "user_input_preview": user_input[:100]},
                )

            return ValidationResult(
                action=ValidationAction.ALLOW,
                validator_name=self.name,
                metadata={"raw_answer": answer},
            )

        except Exception as e:
            # Fail-open: if the classifier is unavailable, allow the request through.
            # The downstream GuardrailMiddleware provides a secondary safety net.
            logger.error("DomainValidator failed (allowing request): %s", e)
            return ValidationResult(
                action=ValidationAction.ALLOW,
                validator_name=self.name,
                message="Domain validation skipped due to classifier error.",
                metadata={"error": str(e)},
            )
