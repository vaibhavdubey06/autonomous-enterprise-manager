from typing import Dict, List, Set
from collections import defaultdict
from app.workflows.models.task import Task

class DependencyResolver:
    @staticmethod
    def validate_dag(tasks: List[Task]) -> bool:
        """Validate if the tasks form a Directed Acyclic Graph (no cycles)."""
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        task_ids = {t.task_id for t in tasks}
        
        for task in tasks:
            in_degree[task.task_id] = len(task.dependencies)
            for dep in task.dependencies:
                if dep not in task_ids:
                    raise ValueError(f"Task {task.task_id} depends on non-existent task {dep}")
                graph[dep].append(task.task_id)
                
        # Kahn's algorithm for topological sorting / cycle detection
        queue = [t_id for t_id in task_ids if in_degree[t_id] == 0]
        visited_count = 0
        
        while queue:
            current = queue.pop(0)
            visited_count += 1
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    
        if visited_count != len(task_ids):
            raise ValueError("Cycle detected in task dependencies")
            
        return True

    @staticmethod
    def get_executable_tasks(tasks: List[Task], completed_task_ids: Set[str]) -> List[Task]:
        """Return tasks that have all dependencies met and are not completed."""
        executable = []
        for task in tasks:
            if task.task_id in completed_task_ids:
                continue
                
            can_execute = True
            for dep in task.dependencies:
                if dep not in completed_task_ids:
                    can_execute = False
                    break
                    
            if can_execute:
                executable.append(task)
                
        return executable
