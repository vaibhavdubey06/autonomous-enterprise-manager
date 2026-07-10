from app.services.llm.models import LLMRequest, LLMConfig
from app.services.llm.providers.base import AbstractLLMProvider
from app.services.llm.router.provider_profile import ProviderProfile
from app.services.llm.router.registry import ProviderRegistry
from app.services.llm.router.provider_health import ProviderHealthService
from app.services.llm.router.routing_policy import RoutingPolicy
from app.services.llm.router.routing_engine import RoutingEngine


class MockProviderA(AbstractLLMProvider):
    def get_profile(self):
        return ProviderProfile(
            provider_name="mock_fast",
            model_name="mock-fast-1",
            vendor="Mock",
            latency_class="fast",
            cost_input=10.0,
            cost_output=10.0,
            quality_score=0.5,
        )

    def generate(self, request):
        pass

    def generate_structured(self, request):
        pass

    async def stream(self, request):
        pass


class MockProviderB(AbstractLLMProvider):
    def get_profile(self):
        return ProviderProfile(
            provider_name="mock_cheap",
            model_name="mock-cheap-1",
            vendor="Mock",
            latency_class="slow",
            cost_input=0.1,
            cost_output=0.1,
            quality_score=0.4,
        )

    def generate(self, request):
        pass

    def generate_structured(self, request):
        pass

    async def stream(self, request):
        pass


class MockProviderC(AbstractLLMProvider):
    def get_profile(self):
        return ProviderProfile(
            provider_name="mock_quality",
            model_name="mock-quality-1",
            vendor="Mock",
            latency_class="medium",
            cost_input=5.0,
            cost_output=5.0,
            quality_score=0.99,
        )

    def generate(self, request):
        pass

    def generate_structured(self, request):
        pass

    async def stream(self, request):
        pass


def test_registry():
    registry = ProviderRegistry()
    provider_a = MockProviderA()
    registry.register(provider_a)

    assert registry.get("mock_fast") is provider_a
    assert len(registry.get_all()) == 1

    registry.remove("mock_fast")
    assert registry.get("mock_fast") is None


def test_routing_engine_policies():
    registry = ProviderRegistry()
    registry.register(MockProviderA())
    registry.register(MockProviderB())
    registry.register(MockProviderC())

    health_svc = ProviderHealthService()
    engine = RoutingEngine(registry, health_svc)

    request = LLMRequest(prompt="Test", config=LLMConfig())

    # Fastest should pick MockProviderA
    fast_provider = engine.select_provider(request, policy=RoutingPolicy.FASTEST)
    assert fast_provider.get_profile().provider_name == "mock_fast"

    # Cheapest should pick MockProviderB
    cheap_provider = engine.select_provider(request, policy=RoutingPolicy.CHEAPEST)
    assert cheap_provider.get_profile().provider_name == "mock_cheap"

    # Highest Quality should pick MockProviderC
    quality_provider = engine.select_provider(
        request, policy=RoutingPolicy.HIGHEST_QUALITY
    )
    assert quality_provider.get_profile().provider_name == "mock_quality"


def test_routing_engine_exclude():
    registry = ProviderRegistry()
    registry.register(MockProviderA())
    registry.register(MockProviderB())

    health_svc = ProviderHealthService()
    engine = RoutingEngine(registry, health_svc)
    request = LLMRequest(prompt="Test", config=LLMConfig())

    # Normally fastest picks A
    fast_provider = engine.select_provider(request, policy=RoutingPolicy.FASTEST)
    assert fast_provider.get_profile().provider_name == "mock_fast"

    # If A is excluded (fallback scenario), it should pick B
    fallback_provider = engine.select_provider(
        request, policy=RoutingPolicy.FASTEST, exclude_providers={"mock_fast"}
    )
    assert fallback_provider.get_profile().provider_name == "mock_cheap"
