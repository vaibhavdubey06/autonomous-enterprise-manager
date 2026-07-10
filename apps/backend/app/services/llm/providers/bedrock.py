import logging
import time
from typing import AsyncGenerator
import requests

from app.services.llm.providers.base import AbstractLLMProvider
from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.router.provider_profile import ProviderProfile
from app.core.config import settings

logger = logging.getLogger(__name__)


def _is_anthropic_model(model_name: str) -> bool:
    """Returns True if the model ID corresponds to an Anthropic Claude model."""
    name = model_name.lower()
    return "anthropic" in name or "claude" in name


class BedrockProvider(AbstractLLMProvider):
    def __init__(self):
        self.bearer_token = (
            settings.AWS_BEARER_TOKEN_BEDROCK
            if hasattr(settings, "AWS_BEARER_TOKEN_BEDROCK")
            else None
        )
        self.model_name = (
            settings.AWS_BEDROCK_MODEL
            if hasattr(settings, "AWS_BEDROCK_MODEL")
            else "eu.anthropic.claude-3-haiku-20240307-v1:0"
        )
        self.region = (
            settings.AWS_REGION if hasattr(settings, "AWS_REGION") else "eu-north-1"
        )

        # URL-encode the model ID. Cross-region profile IDs contain colons and slashes.
        from urllib.parse import quote

        encoded_model = quote(self.model_name, safe="")
        self.base_url = f"https://bedrock-runtime.{self.region}.amazonaws.com/model/{encoded_model}/invoke"

        # Qwen and other non-Anthropic models use the converse/invoke-with-response-stream
        # endpoint with an OpenAI-compatible payload format.
        self._is_anthropic = _is_anthropic_model(self.model_name)
        logger.info(
            f"BedrockProvider: model={self.model_name}, region={self.region}, anthropic={self._is_anthropic}"
        )

        if not self.bearer_token:
            logger.warning("AWS_BEARER_TOKEN_BEDROCK is not set.")

    def get_profile(self) -> ProviderProfile:
        return ProviderProfile(
            provider_name="bedrock",
            model_name=self.model_name,
            vendor="anthropic" if self._is_anthropic else "qwen",
            context_window=128000,
            max_output_tokens=4096,
            supports_json=True,
            supports_streaming=False,
            cost_input=0.003,
            cost_output=0.015,
            latency_class="moderate",
            requests_per_minute=50,
        )

    def _build_anthropic_payload(
        self, prompt: str, max_tokens: int, temperature: float, top_p: float
    ) -> dict:
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "top_p": top_p,
        }

    def _build_qwen_payload(
        self, prompt: str, max_tokens: int, temperature: float, top_p: float
    ) -> dict:
        """OpenAI-compatible payload format used by Qwen and other third-party models on Bedrock."""
        return {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }

    def _parse_response(self, data: dict) -> tuple[str, dict]:
        """Parse both Anthropic and OpenAI-style response formats. Returns (content, usage)."""
        # Anthropic format: {"content": [{"type": "text", "text": "..."}], "usage": {...}}
        if "content" in data and isinstance(data["content"], list):
            content = ""
            for block in data["content"]:
                if block.get("type") == "text":
                    content += block.get("text", "")
            return content, data.get("usage", {})

        # OpenAI-compatible format: {"choices": [{"message": {"content": "..."}}], "usage": {...}}
        if "choices" in data:
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            # Normalise usage keys to Anthropic style so downstream code stays consistent
            normalised_usage = {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            }
            return content, normalised_usage

        # Fallback: try to extract any text field
        return str(data), {}

    def _post(self, payload: dict, timeout: int) -> dict:
        if not self.bearer_token:
            from app.services.llm.exceptions import LLMProviderError

            raise LLMProviderError(
                "Bedrock client not initialized (missing bearer token)"
            )

        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = requests.post(
            self.base_url, headers=headers, json=payload, timeout=timeout
        )
        if not response.ok:
            from app.services.llm.exceptions import LLMProviderError

            raise LLMProviderError(f"Bedrock API error: {response.text}")
        return response.json()

    def generate(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()
        if self._is_anthropic:
            payload = self._build_anthropic_payload(
                request.prompt,
                request.config.max_output_tokens,
                request.config.temperature,
                request.config.top_p,
            )
        else:
            payload = self._build_qwen_payload(
                request.prompt,
                request.config.max_output_tokens,
                request.config.temperature,
                request.config.top_p,
            )

        data = self._post(payload, request.config.timeout)
        content, usage = self._parse_response(data)

        return LLMResponse(
            content=content,
            model_used=self.model_name,
            provider="bedrock",
            latency_ms=(time.time() - start_time) * 1000,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        )

    def generate_structured(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()
        json_prompt = (
            request.prompt
            + "\n\nPlease output ONLY valid JSON without any markdown formatting or extra text."
        )

        if self._is_anthropic:
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": request.config.max_output_tokens,
                "messages": [
                    {"role": "user", "content": json_prompt},
                    {"role": "assistant", "content": "{"},
                ],
                "temperature": request.config.temperature,
                "top_p": request.config.top_p,
            }
        else:
            payload = self._build_qwen_payload(
                json_prompt,
                request.config.max_output_tokens,
                request.config.temperature,
                request.config.top_p,
            )

        data = self._post(payload, request.config.timeout)
        content, usage = self._parse_response(data)

        # For Anthropic, we prefilled '{', so prepend it back
        if self._is_anthropic and not content.startswith("{"):
            content = "{" + content

        return LLMResponse(
            content=content,
            model_used=self.model_name,
            provider="bedrock",
            latency_ms=(time.time() - start_time) * 1000,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        )

    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Streaming not yet implemented for Bedrock")
