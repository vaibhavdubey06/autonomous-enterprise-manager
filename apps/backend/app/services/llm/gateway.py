import logging
import re
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Callable
from pydantic import BaseModel

from app.services.llm.exceptions import (
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMProviderError,
)
from app.services.llm.models import LLMConfig, LLMRequest, LLMResponse, PipelineContext
from app.services.llm.providers.base import AbstractLLMProvider
from app.services.llm.providers.gemini import GeminiProvider
from app.services.llm.pipeline.base import BaseMiddleware
from app.services.llm.pipeline.middlewares import (
    ContextBuilderMiddleware,
    PromptCompilerMiddleware,
    GuardrailMiddleware,
    SchemaValidatorMiddleware,
    TelemetryMiddleware,
    SemanticCacheMiddleware
)

logger = logging.getLogger(__name__)


from app.services.llm.router.routing_engine import RoutingEngine
from app.services.llm.router.routing_policy import RoutingPolicy
from app.services.llm.router.provider_health import provider_health_service

class LLMGateway:
    """
    Enterprise LLM Gateway.
    Acts as the central entry point for all LLM interactions in the platform.
    Implements middleware pipeline and dynamic provider failover.
    """

    def __init__(self, router: Optional[RoutingEngine] = None, middlewares: Optional[List[BaseMiddleware]] = None):
        if router is None:
            from app.services.llm.router.registry import provider_registry
            from app.services.llm.router.provider_health import provider_health_service
            from app.services.llm.providers.gemini import GeminiProvider
            
            # Register Gemini provider by default for backward compatibility
            if not provider_registry.get_all():
                provider_registry.register(GeminiProvider())
            
            router = RoutingEngine(provider_registry, provider_health_service)
            
        self.router = router
        
        # Default middleware pipeline if not provided
        self.middlewares = middlewares if middlewares is not None else [
            TelemetryMiddleware(),
            ContextBuilderMiddleware(),
            SemanticCacheMiddleware(),
            PromptCompilerMiddleware(),
            GuardrailMiddleware(),
            SchemaValidatorMiddleware()
        ]
        
    def _execute_with_fallback(self, func_name: str, ctx: PipelineContext, *args, **kwargs) -> LLMResponse:
        """Dynamic fallback engine that selects alternative providers upon failure."""
        request = ctx.request
        max_retries = request.config.retry_count
        base_delay = 1.0
        exclude_providers = set()
        
        ctx.metadata["fallback_count"] = 0
        ctx.metadata["candidate_count"] = len(self.router.registry.get_all())
        
        # Loop over possible fallback candidates
        # We try up to max_retries different providers if they fail completely
        for attempt in range(1, max_retries + 1):
            try:
                # Select best provider dynamically, excluding failed ones
                policy = RoutingPolicy.BALANCED # default for now, could be dynamic
                provider = self.router.select_provider(request, policy=policy, exclude_providers=exclude_providers)
                func = getattr(provider, func_name)
                
                ctx.metadata["selected_provider"] = provider.get_profile().provider_name
                ctx.metadata["routing_policy"] = policy.value
                ctx.metadata["provider_health"] = self.router.health_service.get_health(provider.get_profile().provider_name).health_score
            except ValueError as e:
                # No more candidates available
                logger.error(f"Routing engine exhausted providers: {e}")
                raise LLMProviderError(f"No available providers: {e}")
                
            try:
                start_time = time.time()
                response = func(request, *args, **kwargs)
                latency = (time.time() - start_time) * 1000
                provider_health_service.record_success(provider.get_profile().provider_name, latency)
                return response
                
            except (LLMRateLimitError, LLMTimeoutError, LLMProviderError) as e:
                provider_name = provider.get_profile().provider_name
                logger.warning(f"Provider '{provider_name}' failed (Attempt {attempt}/{max_retries}): {e}. Adding to exclude list.")
                
                ctx.metadata["fallback_count"] += 1
                
                # Record failure stats
                error_type = "general"
                if isinstance(e, LLMTimeoutError): error_type = "timeout"
                elif isinstance(e, LLMRateLimitError): error_type = "rate_limit"
                
                provider_health_service.record_failure(provider_name, error_type=error_type)
                exclude_providers.add(provider_name)
                
                if attempt == max_retries:
                    logger.error(f"LLM request failed after {max_retries} total fallback attempts.")
                    raise
                
                delay = base_delay * attempt
                time.sleep(delay)
                
            except LLMError as e:
                # Non-retryable errors
                provider_name = provider.get_profile().provider_name
                provider_health_service.record_failure(provider_name, error_type="general")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during LLM generation: {e}")
                raise LLMError(f"Unexpected error: {e}")

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Gateway interface for generating text."""
        context = PipelineContext(request=request)
        
        def _invoke_provider(ctx: PipelineContext) -> None:
            response = self._execute_with_fallback("generate", ctx)
            ctx.response = response
            
        def _build_chain(index: int) -> Callable[[PipelineContext], None]:
            if index == len(self.middlewares):
                return _invoke_provider
            
            middleware = self.middlewares[index]
            next_func = _build_chain(index + 1)
            
            def _execute_middleware(ctx: PipelineContext) -> None:
                middleware.process(ctx, next_func)
                
            return _execute_middleware

        # Execute the pipeline
        pipeline = _build_chain(0)
        pipeline(context)
        
        return context.response

    def generate_structured(self, prompt: str, schema: type[BaseModel], **kwargs) -> str:
        """
        Legacy signature mapping for backward compatibility.
        """
        request = LLMRequest(
            prompt=prompt,
            schema=schema,
            config=LLMConfig(**kwargs)
        )
        
        context = PipelineContext(request=request)
        
        def _invoke_provider(ctx: PipelineContext) -> None:
            response = self._execute_with_fallback("generate_structured", ctx)
            ctx.response = response
            
        def _build_chain(index: int) -> Callable[[PipelineContext], None]:
            if index == len(self.middlewares):
                return _invoke_provider
            
            middleware = self.middlewares[index]
            next_func = _build_chain(index + 1)
            
            def _execute_middleware(ctx: PipelineContext) -> None:
                middleware.process(ctx, next_func)
                
            return _execute_middleware

        # Execute the pipeline
        pipeline = _build_chain(0)
        pipeline(context)
        
        return context.response.content
        
    def _build_legacy_rag_prompt(self, actual_question: str, context: List[str]) -> str:
        """Constructs the strict RAG prompt according to legacy requirements."""
        system_instruction = (
            "You are an Enterprise AI Assistant.\n\n"
            "Rules:\n"
            "- Answer ONLY using the supplied context.\n"
            "- Never use outside knowledge.\n"
            "- Never hallucinate.\n"
            "- If the answer is missing, reply exactly:\n"
            '"I couldn\'t find this information in the uploaded documents."\n'
            "- Keep answers concise.\n"
            "- Use markdown formatting when appropriate.\n"
        )
        context_str = "\n".join(context)
        prompt_structure = (
            "================\n\n"
            "Context\n\n"
            f"{context_str}\n\n"
            "Question\n\n"
            f"{actual_question}\n\n"
            "Answer\n\n"
            "================"
        )
        return system_instruction + "\n" + prompt_structure

    def generate_answer(self, question: str, context: List[str], **kwargs) -> str:
        """
        Legacy signature mapping for backward compatibility.
        Translates the legacy RAG interface into a gateway request.
        """
        # chat_service.py passes a pre-built prompt as the `question` argument.
        match = re.search(r"Question:\s*(.*?)\s*\n\nContext:", question, re.DOTALL)
        actual_question = match.group(1) if match else question
        
        prompt = self._build_legacy_rag_prompt(actual_question, context)
        
        request = LLMRequest(
            prompt=prompt,
            config=LLMConfig(**kwargs)
        )
        
        response = self.generate(request)
        return response.content

    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Gateway interface for streaming responses."""
        raise NotImplementedError("Streaming not yet implemented in the Gateway")
