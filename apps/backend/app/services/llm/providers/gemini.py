import json
import logging
import time
from typing import AsyncGenerator

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.core.config import settings
from app.services.llm.exceptions import (
    LLMAuthenticationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.providers.base import AbstractLLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(AbstractLLMProvider):
    """Google Gemini implementation of the LLM Provider interface."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set.")
        else:
            genai.configure(api_key=self.api_key)

    def get_profile(self):
        from app.services.llm.router.provider_profile import ProviderProfile
        return ProviderProfile(
            provider_name="gemini",
            model_name=settings.GEMINI_MODEL,
            vendor="Google",
            context_window=2000000,
            max_output_tokens=8192,
            supports_json=True,
            supports_streaming=True,
            supports_function_calling=True,
            supports_multimodal=True,
            supports_reasoning=False,
            supports_vision=True,
            supports_embeddings=True,
            supports_audio=True,
            cost_input=0.35,
            cost_output=1.05,
            latency_class="fast",
            quality_score=0.9,
            reliability_score=0.99,
            availability_score=0.99,
            health_status="healthy"
        )

    def _map_exception(self, e: Exception) -> Exception:
        """Map provider-specific exceptions to generic hierarchy."""
        if isinstance(e, google_exceptions.PermissionDenied):
            return LLMAuthenticationError("Gemini API permission denied.")
        elif isinstance(e, google_exceptions.ResourceExhausted):
            return LLMRateLimitError("Gemini API quota exceeded.")
        elif isinstance(e, google_exceptions.DeadlineExceeded):
            return LLMTimeoutError("Gemini API request timed out.")
        elif isinstance(e, google_exceptions.ServiceUnavailable):
            return LLMProviderError("Gemini API service unavailable.")
        return LLMProviderError(f"Unexpected error: {str(e)}")

    def generate(self, request: LLMRequest) -> LLMResponse:
        model_name = request.config.model_name or settings.GEMINI_MODEL
        try:
            model = genai.GenerativeModel(model_name)
        except Exception as e:
            raise LLMProviderError(f"Failed to initialize Gemini model: {e}")

        start_time = time.time()
        
        # Determine actual prompt
        prompt_text = request.prompt
        if request.system_instruction:
            prompt_text = f"{request.system_instruction}\n\n{prompt_text}"

        try:
            response = model.generate_content(
                prompt_text,
                generation_config=genai.types.GenerationConfig(
                    temperature=request.config.temperature,
                    top_p=request.config.top_p,
                    max_output_tokens=request.config.max_output_tokens,
                ),
            )
            latency = (time.time() - start_time) * 1000

            if not response.text:
                raise LLMProviderError("Received empty response text from Gemini.")

            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
            completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)
            total_tokens = getattr(response.usage_metadata, "total_token_count", 0)
            
            from app.services.llm.providers.cost_estimator import CostEstimator
            profile = self.get_profile()
            cost = CostEstimator.calculate_cost(prompt_tokens, completion_tokens, profile.cost_input, profile.cost_output)

            return LLMResponse(
                content=response.text.strip(),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=cost,
                model_used=model_name,
                provider="gemini",
                latency_ms=latency,
            )
        except Exception as e:
            raise self._map_exception(e)

    def generate_structured(self, request: LLMRequest) -> LLMResponse:
        model_name = request.config.model_name or settings.GEMINI_MODEL
        try:
            model = genai.GenerativeModel(model_name)
        except Exception as e:
            raise LLMProviderError(f"Failed to initialize Gemini model: {e}")

        start_time = time.time()
        
        schema_json = json.dumps(request.schema.model_json_schema(), indent=2)
        json_prompt = (
            request.prompt
            + f"\n\nIMPORTANT: You must return ONLY valid, raw JSON matching the following JSON Schema:\n{schema_json}\n\nDo not include markdown formatting or code blocks."
        )

        try:
            response = model.generate_content(
                json_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=request.config.temperature,
                    top_p=request.config.top_p,
                    max_output_tokens=request.config.max_output_tokens,
                ),
            )
            latency = (time.time() - start_time) * 1000

            if not response.text:
                raise LLMProviderError("Received empty response text from Gemini.")

            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
            completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)
            total_tokens = getattr(response.usage_metadata, "total_token_count", 0)
            
            from app.services.llm.providers.cost_estimator import CostEstimator
            profile = self.get_profile()
            cost = CostEstimator.calculate_cost(prompt_tokens, completion_tokens, profile.cost_input, profile.cost_output)

            return LLMResponse(
                content=response.text.strip(),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=cost,
                model_used=model_name,
                provider="gemini",
                latency_ms=latency,
            )
        except Exception as e:
            raise self._map_exception(e)

    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Streaming not yet implemented for GeminiProvider")
