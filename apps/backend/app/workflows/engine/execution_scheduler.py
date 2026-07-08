import logging
from typing import List, Dict, Set
from collections import defaultdict

from app.agents.supervisor.schemas import Task

logger = logging.getLogger(__name__)

class ExecutionScheduler:
    """
    Analyzes task dependencies to determine execution groups for parallel processing.
    Ensures topological sorting and populates the `execution_group` and `dependents` fields.
    """

    @staticmethod
    def schedule(tasks: List[Task]) -> List[Task]:
        """
        Takes a list of tasks (with populated `dependencies`), builds the dependency graph,
        assigns `dependents`, and groups them by topological execution depth (`execution_group`).
        """
        if not tasks:
            return []

        task_map: Dict[str, Task] = {task.task_id: task for task in tasks}
        
        # Build adjacency lists and in-degrees
        adj: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = {task.task_id: 0 for task in tasks}

        for task in tasks:
            # Clean dependencies in case the planner provided unknown IDs
            valid_deps = [dep_id for dep_id in task.dependencies if dep_id in task_map]
            task.dependencies = valid_deps

            for dep_id in valid_deps:
                adj[dep_id].append(task.task_id)
                in_degree[task.task_id] += 1

        # Populate dependents
        for task in tasks:
            task.dependents = adj.get(task.task_id, [])

        # Topological sort using Kahn's algorithm, grouping by depth
        queue: List[str] = [task_id for task_id, deg in in_degree.items() if deg == 0]
        
        # If queue is empty but tasks exist, there is a cycle
        if not queue and tasks:
            logger.error("Cyclic dependency detected in task plan! Falling back to sequential grouping.")
            return ExecutionScheduler._fallback_sequential(tasks)

        current_group = 0
        processed_count = 0

        while queue:
            next_queue = []
            for task_id in queue:
                task = task_map[task_id]
                task.execution_group = current_group
                processed_count += 1
                
                for dependent_id in adj[task_id]:
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        next_queue.append(dependent_id)
                        
            queue = next_queue
            current_group += 1

        if processed_count != len(tasks):
            logger.error("Cyclic dependency detected in task plan during scheduling! Falling back to sequential grouping for remaining tasks.")
            # Assign remaining tasks to sequential groups after the current group
            for task in tasks:
                if in_degree[task.task_id] > 0:
                    task.execution_group = current_group
                    current_group += 1

        return tasks

    @staticmethod
    def _fallback_sequential(tasks: List[Task]) -> List[Task]:
        for i, task in enumerate(tasks):
            task.execution_group = i
            task.dependencies = []
            task.dependents = []
        return tasks
