import pytest
import asyncio
from app.workflows.models.workflow import WorkflowStatus
from app.workflows.models.task import TaskType, TaskStatus
from app.workflows.schemas.workflow import WorkflowCreate
from app.workflows.builder.workflow_builder import WorkflowBuilder
from app.workflows.engine.dependency_resolver import DependencyResolver
from app.workflows.events.in_memory_event_bus import InMemoryEventBus
from app.workflows.events.events import WorkflowEvent, WORKFLOW_STARTED

def test_workflow_builder_creates_valid_workflow():
    builder = WorkflowBuilder(WorkflowCreate(
        goal="Test Goal",
        owner_agent="TestAgent"
    ))
    
    task1 = builder.add_task(name="Task 1")
    task2 = builder.add_task(name="Task 2", dependencies=[task1])
    
    workflow = builder.build()
    
    assert workflow.goal == "Test Goal"
    assert len(workflow.tasks) == 2
    assert workflow.tasks[1].dependencies == [task1]

def test_dependency_resolver_detects_cycles():
    class DummyTask:
        def __init__(self, t_id, deps):
            self.task_id = t_id
            self.dependencies = deps
            
    tasks = [
        DummyTask("1", ["2"]),
        DummyTask("2", ["1"])
    ]
    
    with pytest.raises(ValueError, match="Cycle detected"):
        DependencyResolver.validate_dag(tasks)
        
def test_dependency_resolver_get_executable():
    class DummyTask:
        def __init__(self, t_id, deps):
            self.task_id = t_id
            self.dependencies = deps
            
    t1 = DummyTask("1", [])
    t2 = DummyTask("2", ["1"])
    t3 = DummyTask("3", ["1", "2"])
    
    tasks = [t1, t2, t3]
    
    # Initially only t1 is executable
    exec1 = DependencyResolver.get_executable_tasks(tasks, set())
    assert len(exec1) == 1
    assert exec1[0].task_id == "1"
    
    # After t1 completes, t2 is executable
    exec2 = DependencyResolver.get_executable_tasks(tasks, {"1"})
    assert len(exec2) == 1
    assert exec2[0].task_id == "2"
    
    # After t2 completes, t3 is executable
    exec3 = DependencyResolver.get_executable_tasks(tasks, {"1", "2"})
    assert len(exec3) == 1
    assert exec3[0].task_id == "3"

@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    bus = InMemoryEventBus()
    received_events = []
    
    async def handler(event):
        received_events.append(event)
        
    bus.subscribe(WORKFLOW_STARTED, handler)
    
    bus.publish(WorkflowEvent(
        event_id="test1",
        event_type=WORKFLOW_STARTED,
        workflow_id="wf1"
    ))
    
    # Yield to let async handler run
    await asyncio.sleep(0.01)
    
    assert len(received_events) == 1
    assert received_events[0].workflow_id == "wf1"
