import logging
import json
import time
from typing import AsyncGenerator
import requests

from app.services.llm.providers.base import AbstractLLMProvider
from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.router.provider_profile import ProviderProfile
from app.core.config import settings

logger = logging.getLogger(__name__)

class AnthropicProvider(AbstractLLMProvider):
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY if hasattr(settings, "ANTHROPIC_API_KEY") else None
        self.model_name = settings.ANTHROPIC_MODEL if hasattr(settings, "ANTHROPIC_MODEL") else "claude-3-opus-20240229"
        self.base_url = "https://api.anthropic.com/v1/messages"
        
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY is not set.")

    def get_profile(self) -> ProviderProfile:
        return ProviderProfile(
            provider_name="anthropic",
            model_name=self.model_name,
            vendor="anthropic",
            context_window=200000,
            max_output_tokens=4096,
            supports_json=False,  # Native API uses slightly different JSON format logic if needed
            supports_streaming=True,
            cost_input=0.015,
            cost_output=0.075,
            latency_class="moderate",
            requests_per_minute=50,
        )

    def generate(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()
        
        if not self.api_key:
            from app.services.llm.exceptions import LLMProviderError
            raise LLMProviderError("Anthropic client not initialized (missing API key)")
            
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Anthropic messages API
        payload = {
            "model": self.model_name,
            "max_tokens": request.config.max_output_tokens,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.config.temperature,
            "top_p": request.config.top_p,
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=request.config.timeout)
        
        if not response.ok:
            from app.services.llm.exceptions import LLMProviderError
            raise LLMProviderError(f"Anthropic API error: {response.text}")
            
        data = response.json()
        
        # Parse the response text
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
                
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=content,
            model_used=self.model_name,
            provider="anthropic",
            latency_ms=(time.time() - start_time) * 1000,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        )

    def generate_structured(self, request: LLMRequest) -> LLMResponse:
        # Anthropic does not have a strict JSON mode flag in the same way OpenAI/OpenRouter do,
        # but we can force it by appending instructions and prefilling the assistant's message with '{'
        start_time = time.time()
        
        if not self.api_key:
            from app.services.llm.exceptions import LLMProviderError
            raise LLMProviderError("Anthropic client not initialized (missing API key)")
            
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "max_tokens": request.config.max_output_tokens,
            "messages": [
                {"role": "user", "content": request.prompt + "\n\nPlease output ONLY valid JSON without any markdown formatting or extra text."},
                {"role": "assistant", "content": "{"}
            ],
            "temperature": request.config.temperature,
            "top_p": request.config.top_p,
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=request.config.timeout)
        
        if not response.ok:
            from app.services.llm.exceptions import LLMProviderError
            raise LLMProviderError(f"Anthropic API error: {response.text}")
            
        data = response.json()
        
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
                
        # We prefilled '{', so we prepend it back to the response content
        content = "{" + content
        
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=content,
            model_used=self.model_name,
            provider="anthropic",
            latency_ms=(time.time() - start_time) * 1000,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        )

    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Streaming not yet implemented for Anthropic")
