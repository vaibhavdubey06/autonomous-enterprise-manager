import logging
from typing import AsyncGenerator
import requests
from pydantic import BaseModel

from app.services.llm.providers.base import AbstractLLMProvider
from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.router.provider_profile import ProviderProfile
from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenRouterProvider(AbstractLLMProvider):
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY if hasattr(settings, "OPENROUTER_API_KEY") else None
        self.model_name = settings.OPENROUTER_MODEL if hasattr(settings, "OPENROUTER_MODEL") else "google/gemini-2.0-flash-exp:free"
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY is not set.")

    def get_profile(self) -> ProviderProfile:
        return ProviderProfile(
            provider_name="openrouter",
            model_name=self.model_name,
            vendor="openrouter",
            context_window=32000,
            max_output_tokens=4096,
            supports_json=True,
            supports_streaming=True,
            cost_input=0.0,
            cost_output=0.0,
            latency_class="fast",
            requests_per_minute=200,
        )

    def generate(self, request: LLMRequest) -> LLMResponse:
        import time
        start_time = time.time()
        
        if not self.api_key:
            from app.services.llm.exceptions import LLMProviderError
            raise LLMProviderError("OpenRouter client not initialized (missing API key)")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "AEM",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.config.temperature,
            "top_p": request.config.top_p,
            "max_tokens": request.config.max_output_tokens,
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=request.config.timeout)
        
        if not response.ok:
            from app.services.llm.exceptions import LLMProviderError
            raise LLMProviderError(f"OpenRouter API error: {response.text}")
            
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=content,
            model_used=self.model_name,
            provider="openrouter",
            latency_ms=(time.time() - start_time) * 1000,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

    def generate_structured(self, request: LLMRequest) -> LLMResponse:
        import time
        start_time = time.time()
        
        if not self.api_key:
            from app.services.llm.exceptions import LLMProviderError
            raise LLMProviderError("OpenRouter client not initialized (missing API key)")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "AEM",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.config.temperature,
            "top_p": request.config.top_p,
            "max_tokens": request.config.max_output_tokens,
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=request.config.timeout)
        
        if not response.ok:
            from app.services.llm.exceptions import LLMProviderError
            raise LLMProviderError(f"OpenRouter API error: {response.text}")
            
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=content,
            model_used=self.model_name,
            provider="openrouter",
            latency_ms=(time.time() - start_time) * 1000,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Streaming not yet implemented for OpenRouter")
