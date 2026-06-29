"""Unit tests for Enterprise Platform Services (Phase 16)."""

import pytest

# --- Event Platform Tests ---
from app.events.base.interfaces import DomainEvent, EventPriority
from app.events.bus.in_memory_event_bus import InMemoryEventBus
from app.events.schemas.domain_events import (
    WorkflowCompletedEvent,
    PolicyViolationEvent,
    SecurityIncidentEvent,
)


def test_domain_event_creation():
    event = DomainEvent(
        event_type="test.event",
        payload={"key": "value"},
        source="test",
    )
    assert event.event_type == "test.event"
    assert event.payload == {"key": "value"}
    assert event.source == "test"
    assert event.correlation_id is not None
    assert event.version == 1
    d = event.to_dict()
    assert d["event_type"] == "test.event"


def test_in_memory_event_bus_publish_subscribe():
    bus = InMemoryEventBus()
    received = []

    def handler(event: DomainEvent):
        received.append(event)

    bus.subscribe("test.event", handler)
    event = DomainEvent(event_type="test.event", payload={}, source="test")
    bus.publish(event)

    assert len(received) == 1
    assert received[0].event_type == "test.event"


def test_event_bus_wildcard_subscriber():
    bus = InMemoryEventBus()
    received = []

    bus.subscribe("*", lambda e: received.append(e))
    bus.publish(DomainEvent(event_type="a", payload={}, source="test"))
    bus.publish(DomainEvent(event_type="b", payload={}, source="test"))

    assert len(received) == 2


def test_event_bus_unsubscribe():
    bus = InMemoryEventBus()
    received = []

    def handler(e):
        received.append(e)

    bus.subscribe("test", handler)
    bus.unsubscribe("test", handler)
    bus.publish(DomainEvent(event_type="test", payload={}, source="test"))

    assert len(received) == 0


def test_event_bus_history():
    bus = InMemoryEventBus()
    for i in range(5):
        bus.publish(DomainEvent(event_type="test", payload={"i": i}, source="test"))

    history = bus.get_history()
    assert len(history) == 5

    history_limited = bus.get_history(limit=3)
    assert len(history_limited) == 3


def test_domain_events_workflow_completed():
    event = WorkflowCompletedEvent("wf-1", {"status": "success"})
    assert event.event_type == "workflow.completed"
    assert event.payload["workflow_id"] == "wf-1"


def test_domain_events_policy_violation():
    event = PolicyViolationEvent("pol-1", "Budget exceeded")
    assert event.priority == EventPriority.HIGH


def test_domain_events_security_incident():
    event = SecurityIncidentEvent("brute_force", {"ip": "1.2.3.4"})
    assert event.priority == EventPriority.CRITICAL


# --- Scheduler Tests ---
from app.scheduler.scheduler_service import (
    ScheduledJob,
    SchedulerService,
    JobStatus,
)


def test_scheduler_register_and_execute():
    scheduler = SchedulerService()
    job = ScheduledJob(name="test_job", handler=lambda: "done")
    job_id = scheduler.register_job(job)

    result = scheduler.execute_job(job_id)
    assert result["status"] == "completed"


def test_scheduler_job_failure_and_retry():
    scheduler = SchedulerService()
    call_count = 0

    def failing_handler():
        nonlocal call_count
        call_count += 1
        raise Exception("fail")

    job = ScheduledJob(name="flaky_job", handler=failing_handler, max_retries=2)
    job_id = scheduler.register_job(job)

    result = scheduler.execute_job(job_id)
    assert result["status"] == "failed"
    assert len(scheduler.get_retry_queue()) == 1


def test_scheduler_cancel_job():
    scheduler = SchedulerService()
    job = ScheduledJob(name="cancel_me", handler=lambda: None)
    job_id = scheduler.register_job(job)

    assert scheduler.cancel_job(job_id) is True
    jobs = scheduler.list_jobs(status=JobStatus.CANCELLED)
    assert len(jobs) == 1


def test_scheduler_list_jobs():
    scheduler = SchedulerService()
    scheduler.register_job(ScheduledJob(name="j1", handler=lambda: None))
    scheduler.register_job(ScheduledJob(name="j2", handler=lambda: None))

    all_jobs = scheduler.list_jobs()
    assert len(all_jobs) == 2


# --- LLM Platform Tests ---
from app.llm.providers.base import (
    InferenceRequest,
    InferenceResponse,
    LLMProvider,
    ModelCapability,
)
from app.llm.routing.routing_engine import (
    ModelEntry,
    ModelRegistry,
    ProviderRegistry,
    RoutingEngine,
)


class MockProvider(LLMProvider):
    def __init__(self, name: str, available: bool = True):
        self._name = name
        self._available = available

    def get_name(self) -> str:
        return self._name

    def get_supported_models(self):
        return [f"{self._name}-model"]

    def get_capabilities(self):
        return [ModelCapability.TEXT_GENERATION, ModelCapability.REASONING]

    def invoke(self, request: InferenceRequest) -> InferenceResponse:
        return InferenceResponse(
            content=f"Response from {self._name}",
            provider=self._name,
            model=f"{self._name}-model",
            tokens_used=100,
        )

    def is_available(self) -> bool:
        return self._available


def test_provider_registry():
    registry = ProviderRegistry()
    provider = MockProvider("test-provider")
    registry.register(provider)

    assert "test-provider" in registry.list_providers()
    assert registry.get_provider("test-provider") is provider


def test_model_registry():
    registry = ModelRegistry()
    entry = ModelEntry(
        model_id="test-model",
        provider_name="test-provider",
        capabilities=[ModelCapability.TEXT_GENERATION],
        is_default=True,
    )
    registry.register(entry)

    assert registry.get_model("test-model") is entry
    assert registry.get_default_model() is entry


def test_routing_engine_basic():
    pr = ProviderRegistry()
    mr = ModelRegistry()
    provider = MockProvider("gemini")
    pr.register(provider)

    engine = RoutingEngine(pr, mr)
    request = InferenceRequest(
        prompt="Hello", capability=ModelCapability.TEXT_GENERATION
    )
    response = engine.route(request)

    assert response.provider == "gemini"
    assert "Response from" in response.content


def test_routing_engine_fallback():
    pr = ProviderRegistry()
    mr = ModelRegistry()

    class FailingProvider(MockProvider):
        def invoke(self, request):
            raise Exception("Provider down")

    pr.register(FailingProvider("failing", available=True))
    pr.register(MockProvider("backup", available=True))

    engine = RoutingEngine(pr, mr)
    request = InferenceRequest(
        prompt="Hello", capability=ModelCapability.TEXT_GENERATION
    )
    response = engine.route(request)
    assert response.provider == "backup"


def test_routing_engine_no_provider_raises():
    pr = ProviderRegistry()
    mr = ModelRegistry()
    engine = RoutingEngine(pr, mr)

    with pytest.raises(RuntimeError, match="No available provider"):
        engine.route(
            InferenceRequest(prompt="Hello", capability=ModelCapability.EMBEDDING)
        )


# --- Plugin SDK Tests ---
from app.plugins.plugin_sdk import (
    PluginContext,
    PluginHook,
    PluginManifest,
    PluginRegistry,
    PluginType,
)


def test_plugin_register_and_list():
    registry = PluginRegistry()
    manifest = PluginManifest(
        name="TestPlugin",
        version="1.0.0",
        plugin_type=PluginType.CONNECTOR,
        description="A test plugin",
    )
    registry.register(manifest)

    plugins = registry.list_plugins()
    assert len(plugins) == 1
    assert plugins[0]["name"] == "TestPlugin"
    assert plugins[0]["status"] == "discovered"


def test_plugin_activate_and_deactivate():
    registry = PluginRegistry()

    class TestHook(PluginHook):
        def __init__(self):
            self.loaded = False

        def on_load(self, context):
            self.loaded = True

        def on_unload(self):
            self.loaded = False

    hook = TestHook()
    manifest = PluginManifest(
        name="HookPlugin", version="1.0.0", plugin_type=PluginType.AGENT
    )
    plugin_id = registry.register(manifest, hook)

    ctx = PluginContext(config={}, services={})
    assert registry.activate(plugin_id, ctx) is True
    assert hook.loaded is True

    info = registry.get_plugin(plugin_id)
    assert info["status"] == "active"

    registry.deactivate(plugin_id)
    assert hook.loaded is False


def test_plugin_filter_by_type():
    registry = PluginRegistry()
    registry.register(
        PluginManifest(name="A", version="1.0", plugin_type=PluginType.AGENT)
    )
    registry.register(
        PluginManifest(name="B", version="1.0", plugin_type=PluginType.CONNECTOR)
    )

    agents = registry.list_plugins(plugin_type=PluginType.AGENT)
    assert len(agents) == 1
    assert agents[0]["name"] == "A"


# --- Configuration & Metadata Tests ---
from app.configuration.config_metadata_platform import (
    ConfigurationRegistry,
    MetadataEntry,
    MetadataRegistry,
)


def test_configuration_registry():
    config = ConfigurationRegistry()
    config.set("key1", "value1")
    assert config.get("key1") == "value1"
    assert config.get("missing", "default") == "default"


def test_feature_flags():
    config = ConfigurationRegistry()
    config.register_flag("beta_feature", enabled=False, description="Beta")

    assert config.is_enabled("beta_feature") is False
    config.toggle_flag("beta_feature")
    assert config.is_enabled("beta_feature") is True

    flags = config.list_flags()
    assert len(flags) == 1


def test_version_registry():
    config = ConfigurationRegistry()
    config.register_version("prompt", "cto_report", "2.1.0")
    assert config.get_version("prompt", "cto_report") == "2.1.0"


def test_metadata_registry():
    registry = MetadataRegistry()
    entry = MetadataEntry(
        asset_type="workflow",
        asset_id="wf-1",
        name="Repository Review",
        owner="cto",
        tags=["devops", "review"],
        domain="engineering",
    )
    registry.register(entry)

    result = registry.get_by_asset("workflow", "wf-1")
    assert result is not None
    assert result["name"] == "Repository Review"


def test_metadata_search():
    registry = MetadataRegistry()
    registry.register(
        MetadataEntry(
            asset_type="agent",
            asset_id="a1",
            name="CTO Agent",
            domain="engineering",
            tags=["executive"],
        )
    )
    registry.register(
        MetadataEntry(
            asset_type="connector",
            asset_id="c1",
            name="GitHub",
            domain="engineering",
            tags=["devops"],
        )
    )

    results = registry.search(domain="engineering")
    assert len(results) == 2

    results = registry.search(tag="executive")
    assert len(results) == 1


# --- Decision Intelligence Tests ---
from app.decisions.decision_platform import (
    DecisionCategory,
    DecisionRecord,
    DecisionRegistry,
    DecisionStatus,
)


def test_decision_create_and_get():
    registry = DecisionRegistry()
    record = DecisionRecord(
        title="Use LangGraph",
        category=DecisionCategory.ARCHITECTURE,
        context="Need workflow orchestration",
        problem="No workflow engine",
        decision="Adopt LangGraph",
        rationale="Best fit for agent workflows",
        confidence=0.95,
    )
    decision_id = registry.create(record)

    result = registry.get(decision_id)
    assert result is not None
    assert result["title"] == "Use LangGraph"
    assert result["confidence"] == 0.95


def test_decision_update_status():
    registry = DecisionRegistry()
    record = DecisionRecord(
        title="Test",
        category=DecisionCategory.TECHNOLOGY,
        context="ctx",
        problem="prob",
        decision="dec",
        rationale="rat",
    )
    did = registry.create(record)

    assert registry.update_status(did, DecisionStatus.APPROVED) is True
    assert registry.get(did)["status"] == "approved"


def test_decision_record_outcome():
    registry = DecisionRegistry()
    record = DecisionRecord(
        title="Budget",
        category=DecisionCategory.BUDGET,
        context="ctx",
        problem="prob",
        decision="dec",
        rationale="rat",
    )
    did = registry.create(record)

    registry.record_outcome(did, "Successfully deployed within budget")
    result = registry.get(did)
    assert result["status"] == "implemented"
    assert result["outcome"] == "Successfully deployed within budget"


def test_decision_search():
    registry = DecisionRegistry()
    registry.create(
        DecisionRecord(
            title="Adopt Qdrant",
            category=DecisionCategory.TECHNOLOGY,
            context="Need vector store",
            problem="No vector DB",
            decision="Use Qdrant",
            rationale="Fast and scalable",
        )
    )
    registry.create(
        DecisionRecord(
            title="Multi-tenant model",
            category=DecisionCategory.ARCHITECTURE,
            context="Enterprise multi-tenancy",
            problem="Tenant isolation",
            decision="Schema-per-tenant",
            rationale="Strong isolation",
        )
    )

    results = registry.search(category=DecisionCategory.TECHNOLOGY)
    assert len(results) == 1
    assert results[0]["title"] == "Adopt Qdrant"

    results = registry.search(query="multi-tenant")
    assert len(results) == 1
