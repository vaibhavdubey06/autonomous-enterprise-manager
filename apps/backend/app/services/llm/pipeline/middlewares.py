import json
import logging
from typing import Callable

from pydantic import ValidationError

from app.operations.tracing.trace_manager import TraceManager
from app.operations.telemetry.telemetry_context import TelemetryContext
from app.services.llm.exceptions import LLMValidationError
from app.services.llm.models import PipelineContext
from app.services.llm.pipeline.base import BaseMiddleware

logger = logging.getLogger(__name__)


from app.services.llm.context.builder import ContextBuilder
from app.services.llm.prompts.compiler import PromptCompiler
from app.services.llm.models import LLMResponse
from app.services.cache.models import CacheKey, CacheMetadata
from app.services.cache.semantic_cache import SemanticCacheService

class SemanticCacheMiddleware(BaseMiddleware):
    def __init__(self):
        self.cache_service = SemanticCacheService()

    def process(self, context: PipelineContext, next_middleware: Callable[[PipelineContext], None]) -> None:
        telemetry_snap = TelemetryContext.get_snapshot()
        trace_id = telemetry_snap.get("trace_id")
        
        # Build Cache Key
        enterprise_context = context.metadata.get("context_data")
        chunk_ids = []
        chunk_hashes = []
        if enterprise_context and hasattr(enterprise_context, "retrieved_documents"):
            for doc in enterprise_context.retrieved_documents:
                chunk_ids.append(getattr(doc, "id", ""))
                chunk_hashes.append(getattr(doc, "hash", getattr(doc, "id", "")))
                
        key = CacheKey(
            user_question=context.request.prompt,
            tenant_id=context.metadata.get("tenant_id", "default"),
            retrieved_chunk_ids=chunk_ids,
            retrieved_chunk_hashes=chunk_hashes
        )
        
        # Cache Lookup
        entry = self.cache_service.lookup(key, trace_id=trace_id)
        if entry:
            context.response = LLMResponse(
                content=entry.response_content,
                provider="cache",
                model_used="cache",
                latency_ms=0.0,
                cached=True,
                estimated_cost=0.0
            )
            return  # Short-circuit pipeline
            
        # Cache Miss
        next_middleware(context)
        
        # Post-Process: Store cache
        if context.response and not getattr(context.response, "cached", False):
            metadata = CacheMetadata(
                token_usage=getattr(context.response, "token_usage", 0),
                estimated_cost=getattr(context.response, "estimated_cost", 0.0),
                model=getattr(context.response, "model_used", "unknown"),
                provider=getattr(context.response, "provider", "unknown"),
                tenant_id=key.tenant_id
            )
            self.cache_service.store_async(
                key=key,
                question=context.request.prompt,
                response=context.response.content,
                metadata=metadata,
                trace_id=trace_id
            )

class ContextBuilderMiddleware(BaseMiddleware):
    """Builds enterprise context using the ContextBuilder."""
    
    def __init__(self):
        self.builder = ContextBuilder()
        
    def process(self, context: PipelineContext, next_middleware: Callable[[PipelineContext], None]) -> None:
        telemetry_snap = TelemetryContext.get_snapshot()
        trace_manager = TraceManager()
        span = trace_manager.start_span(
            trace_id=telemetry_snap.get("trace_id"),
            operation="build_context",
            parent_span_id=telemetry_snap.get("span_id")
        )
        
        try:
            enterprise_context = self.builder.build_context(context.request, context.metadata)
            context.metadata["context_data"] = enterprise_context
            
            span.attributes["context_elements"] = len(enterprise_context.retrieved_documents) + len(enterprise_context.semantic_memory)
            trace_manager.end_span(span, "OK")
        except Exception as e:
            trace_manager.end_span(span, "ERROR")
            raise
            
        next_middleware(context)


class PromptCompilerMiddleware(BaseMiddleware):
    """Compiles prompt assets using the PromptCompiler."""
    
    def __init__(self):
        self.compiler = PromptCompiler()
        
    def process(self, context: PipelineContext, next_middleware: Callable[[PipelineContext], None]) -> None:
        telemetry_snap = TelemetryContext.get_snapshot()
        trace_manager = TraceManager()
        span = trace_manager.start_span(
            trace_id=telemetry_snap.get("trace_id"),
            operation="compile_prompt",
            parent_span_id=telemetry_snap.get("span_id")
        )
        
        try:
            enterprise_context = context.metadata.get("context_data")
            # Fallback if ContextBuilder didn't run or failed silently
            if not enterprise_context:
                from app.services.llm.context.models import EnterpriseContext
                enterprise_context = EnterpriseContext()
                
            compiled_prompt = self.compiler.compile(context.request, enterprise_context)
            
            # Mutate the request prompt to be the final compiled string before hitting the provider
            context.request.prompt = compiled_prompt.text
            
            # Save compilation metadata for downstream telemetry or debugging
            context.metadata["compiled_prompt"] = compiled_prompt
            
            span.attributes["asset_id"] = compiled_prompt.asset_id or "anonymous"
            span.attributes["prompt_length"] = len(compiled_prompt.text)
            trace_manager.end_span(span, "OK")
        except Exception as e:
            span.attributes["error"] = str(e)
            trace_manager.end_span(span, "ERROR")
            raise
            
        next_middleware(context)


from app.services.llm.guardrails.engine import GuardrailEngine
from app.services.llm.guardrails.models import PolicyAction
from app.services.llm.guardrails.detectors.injection import PromptInjectionDetector
from app.services.llm.guardrails.detectors.jailbreak import JailbreakDetector
from app.services.llm.guardrails.detectors.secrets import SecretDetector
from app.services.llm.guardrails.detectors.pii import PIIDetector
from app.services.llm.guardrails.detectors.prompt_length import PromptLengthDetector
from app.services.llm.guardrails.detectors.json import JSONValidator
from app.services.llm.guardrails.detectors.citation import CitationPresenceValidator
from app.services.llm.guardrails.detectors.response_length import ResponseLengthValidator
from app.services.llm.guardrails.detectors.hallucination import HallucinationValidator
from app.services.llm.exceptions import GuardrailException

class GuardrailMiddleware(BaseMiddleware):
    """Executes Enterprise Guardrails on incoming requests and outgoing responses."""
    
    def __init__(self):
        self.engine = GuardrailEngine(detectors=[
            PromptInjectionDetector(),
            JailbreakDetector(),
            SecretDetector(),
            PIIDetector(),
            PromptLengthDetector(),
            JSONValidator(),
            CitationPresenceValidator(),
            ResponseLengthValidator(),
            HallucinationValidator()
        ])

    def process(self, context: PipelineContext, next_middleware: Callable[[PipelineContext], None]) -> None:
        # Evaluate Request
        req_result = self.engine.evaluate_request(context.request, context.metadata)
        if req_result.action == PolicyAction.BLOCK:
            raise GuardrailException("Request blocked by guardrails.", req_result.findings)
            
        next_middleware(context)
        
        # Evaluate Response
        if context.response:
            resp_result = self.engine.evaluate_response(context.request, context.response, context.metadata)
            if resp_result.action == PolicyAction.BLOCK:
                raise GuardrailException("Response blocked by guardrails.", resp_result.findings)



class SchemaValidatorMiddleware(BaseMiddleware):
    """Validates structured outputs against the requested Pydantic schema."""
    def process(self, context: PipelineContext, next_middleware: Callable[[PipelineContext], None]) -> None:
        # Pre-process: none required
        next_middleware(context)
        
        # Post-process: Validate if schema was requested
        if context.request.schema and context.response:
            try:
                # Assuming the LLM output is a JSON string
                # We attempt to load and validate it
                parsed_json = json.loads(context.response.content)
                context.request.schema.model_validate(parsed_json)
                
                # If we wanted to, we could attach the validated object to context.metadata
                # But typically we return the raw string and let the caller parse it, 
                # or we just ensure it's valid. Here we just ensure it's valid.
            except json.JSONDecodeError as e:
                raise LLMValidationError(f"LLM did not return valid JSON. Error: {e}\nContent: {context.response.content}")
            except ValidationError as e:
                raise LLMValidationError(f"LLM output failed schema validation. Error: {e}\nContent: {context.response.content}")


class TelemetryMiddleware(BaseMiddleware):
    """Integrates LLM Gateway with the existing TraceManager and TelemetryContext."""
    
    def __init__(self):
        self.trace_manager = TraceManager()

    def process(self, context: PipelineContext, next_middleware: Callable[[PipelineContext], None]) -> None:
        telemetry_snap = TelemetryContext.get_snapshot()
        trace_id = telemetry_snap.get("trace_id")
        parent_span_id = telemetry_snap.get("span_id")
        
        attributes = {
            "model_requested": context.request.config.model_name or "default",
            "temperature": context.request.config.temperature,
            "tokens_max": context.request.config.max_output_tokens,
            "provider": "gemini" # default until abstracted further
        }

        # If there's no trace_id, we just start a new trace
        if not trace_id:
            span = self.trace_manager.start_trace("llm_generation", **attributes)
        else:
            span = self.trace_manager.start_span(
                trace_id=trace_id,
                operation="llm_generation",
                parent_span_id=parent_span_id,
                **attributes
            )
            
        try:
            # Proceed with the pipeline
            next_middleware(context)
            
            # Enrich span on success
            if context.response:
                span.attributes["latency_ms"] = context.response.latency_ms
                span.attributes["model_used"] = context.response.model_used
                span.attributes["provider"] = context.response.provider
                span.attributes["cached"] = getattr(context.response, "cached", False)
                span.attributes["estimated_cost"] = getattr(context.response, "estimated_cost", 0.0)
                
            # Router specific metrics added by the Gateway fallback engine
            if "fallback_count" in context.metadata:
                span.attributes["fallback_count"] = context.metadata["fallback_count"]
            if "candidate_count" in context.metadata:
                span.attributes["candidate_count"] = context.metadata["candidate_count"]
            if "selected_provider" in context.metadata:
                span.attributes["selected_provider"] = context.metadata["selected_provider"]
            if "routing_policy" in context.metadata:
                span.attributes["routing_policy"] = context.metadata["routing_policy"]
            if "provider_health" in context.metadata:
                span.attributes["provider_health_score"] = context.metadata["provider_health"]
                
            self.trace_manager.end_span(span, "OK")
        except Exception as e:
            span.attributes["error"] = str(e)
            span.attributes["error_type"] = type(e).__name__
            self.trace_manager.end_span(span, "ERROR")
            raise
