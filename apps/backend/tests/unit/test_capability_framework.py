import pytest
from app.capabilities.base.schemas import Capability, CapabilityType, CapabilityResult
from app.capabilities.base.base_capability import BaseCapability
from app.capabilities.base.capability_registry import CapabilityRegistry
from app.capabilities.base.executor import CapabilityExecutor
from app.capabilities.tools.github.tool import GitHubCapability
from app.capabilities.tools.github.actions import GitHubAction

class DummyCapability(BaseCapability):
    def get_metadata(self) -> Capability:
        return Capability(
            capability_id="dummy",
            name="Dummy",
            description="A dummy capability",
            type=CapabilityType.TOOL,
            supported_actions=["do_something"],
            supported_agents=["TestAgent"]
        )
        
    def _execute_internal(self, action, kwargs):
        if action == "do_something":
            return {"result": "success"}
        raise ValueError("Unsupported")

def test_capability_registry():
    registry = CapabilityRegistry()
    cap = DummyCapability()
    registry.register(cap)
    
    assert registry.get("dummy") is cap
    assert len(registry.list()) == 1
    
    matching_agent = registry.find_by_agent("TestAgent")
    assert len(matching_agent) == 1
    
    matching_action = registry.find_by_action("do_something")
    assert len(matching_action) == 1
    
    registry.unregister("dummy")
    assert registry.get("dummy") is None

def test_capability_executor_success():
    registry = CapabilityRegistry()
    registry.register(DummyCapability())
    executor = CapabilityExecutor(registry)
    
    result = executor.execute("TestAgent", "dummy", "do_something")
    assert result.success is True
    assert result.data == {"result": "success"}
    assert "Executing do_something..." in result.logs

def test_capability_executor_unauthorized():
    registry = CapabilityRegistry()
    registry.register(DummyCapability())
    executor = CapabilityExecutor(registry)
    
    result = executor.execute("HackerAgent", "dummy", "do_something")
    assert result.success is False
    assert "is not authorized" in result.errors[0]

def test_capability_executor_not_found():
    registry = CapabilityRegistry()
    executor = CapabilityExecutor(registry)
    
    result = executor.execute("TestAgent", "nonexistent", "do_something")
    assert result.success is False
    assert "not found" in result.errors[0]

def test_github_capability_metadata():
    gh = GitHubCapability()
    meta = gh.get_metadata()
    assert meta.capability_id == "github_tool"
    assert GitHubAction.INDEX_REPOSITORY.value in meta.supported_actions

def test_github_capability_execute_not_implemented():
    gh = GitHubCapability()
    # We bypass executor for direct unit test
    result = gh.execute("CTO Agent", GitHubAction.CREATE_ISSUE.value, repository_name="test")
    assert result.success is True
    assert result.data["status"] == "Not Implemented"
