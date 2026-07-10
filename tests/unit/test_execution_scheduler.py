from app.workflows.engine.execution_scheduler import ExecutionScheduler
from app.agents.supervisor.schemas import Task


def test_execution_scheduler_independent_tasks():
    t1 = Task(goal="t1", description="", dependencies=[])
    t2 = Task(goal="t2", description="", dependencies=[])
    t3 = Task(goal="t3", description="", dependencies=[])

    tasks = ExecutionScheduler.schedule([t1, t2, t3])

    # All independent tasks should be in execution_group 0
    assert tasks[0].execution_group == 0
    assert tasks[1].execution_group == 0
    assert tasks[2].execution_group == 0


def test_execution_scheduler_sequential_chain():
    t1 = Task(goal="t1", description="", dependencies=[])
    t2 = Task(goal="t2", description="", dependencies=[t1.task_id])
    t3 = Task(goal="t3", description="", dependencies=[t2.task_id])

    ExecutionScheduler.schedule([t1, t2, t3])

    assert t1.execution_group == 0
    assert t2.execution_group == 1
    assert t3.execution_group == 2
    assert t1.task_id in t2.dependencies
    assert t2.task_id in t3.dependencies
    assert t2.task_id in t1.dependents
    assert t3.task_id in t2.dependents


def test_execution_scheduler_complex_graph():
    # t1  t2
    #  \  /
    #   t3
    #   |
    #   t4
    t1 = Task(goal="t1", description="", dependencies=[])
    t2 = Task(goal="t2", description="", dependencies=[])
    t3 = Task(goal="t3", description="", dependencies=[t1.task_id, t2.task_id])
    t4 = Task(goal="t4", description="", dependencies=[t3.task_id])

    ExecutionScheduler.schedule([t1, t2, t3, t4])

    assert t1.execution_group == 0
    assert t2.execution_group == 0
    assert t3.execution_group == 1
    assert t4.execution_group == 2


def test_execution_scheduler_cycle_fallback():
    t1 = Task(goal="t1", description="", dependencies=[])
    t2 = Task(goal="t2", description="", dependencies=[t1.task_id])

    # Manually creating a cycle
    t1.dependencies.append(t2.task_id)

    ExecutionScheduler.schedule([t1, t2])

    assert t1.execution_group == 0
    assert t2.execution_group == 1
