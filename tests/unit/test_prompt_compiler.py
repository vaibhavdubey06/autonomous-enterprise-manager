import pytest
from app.services.llm.models import LLMRequest, LLMConfig
from app.services.llm.context.builder import ContextBuilder
from app.services.llm.context.models import EnterpriseContext
from app.services.llm.prompts.models import PromptAsset
from app.services.llm.prompts.registry import prompt_registry
from app.services.llm.prompts.compiler import PromptCompiler


def test_context_builder():
    builder = ContextBuilder()
    request = LLMRequest(
        prompt="Test",
        context=["retrieved_doc_1"],
        metadata={"workflow_state": {"status": "in_progress"}},
        config=LLMConfig(),
    )

    additional_metadata = {"execution_context": {"agent_id": "test_agent"}}

    context = builder.build_context(request, additional_metadata)

    assert context.retrieved_documents == ["retrieved_doc_1"]
    assert context.workflow_state == {"status": "in_progress"}
    assert context.execution_context == {"agent_id": "test_agent"}


def test_prompt_compiler_anonymous():
    compiler = PromptCompiler()
    request = LLMRequest(
        prompt="Hello $name",
        metadata={"variables": {"name": "Alice"}},
        config=LLMConfig(),
    )
    context = EnterpriseContext(semantic_memory=["User likes Python."])

    compiled = compiler.compile(request, context)

    assert compiled.asset_id == "anonymous"
    assert "Hello Alice" in compiled.text
    assert "User likes Python." in compiled.text


def test_prompt_compiler_registry():
    asset = PromptAsset(
        id="test_greeting", description="test", template="Greeting: $greeting"
    )
    prompt_registry.register(asset)

    compiler = PromptCompiler()
    request = LLMRequest(
        prompt="Ignored because template_id is set",
        metadata={
            "template_id": "test_greeting",
            "variables": {"greeting": "Hi there!"},
            "prompt_strategy": "chat",
        },
        config=LLMConfig(),
    )
    context = EnterpriseContext(workflow_state={"status": "ready"})

    compiled = compiler.compile(request, context)

    assert compiled.asset_id == "test_greeting"
    assert "Greeting: Hi there!" in compiled.text
    assert "Workflow State:" in compiled.text
    assert "ready" in compiled.text


def test_prompt_compiler_missing_asset():
    compiler = PromptCompiler()
    request = LLMRequest(
        prompt="", metadata={"template_id": "nonexistent_asset"}, config=LLMConfig()
    )
    context = EnterpriseContext()

    with pytest.raises(ValueError, match="not found in registry"):
        compiler.compile(request, context)
