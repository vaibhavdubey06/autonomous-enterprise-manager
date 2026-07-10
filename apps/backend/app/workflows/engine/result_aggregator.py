import logging
from typing import List, Dict, Any
from app.agents.supervisor.schemas import Task

logger = logging.getLogger(__name__)


class ResultAggregator:
    """
    Deterministically merges and aggregates results from parallel tasks.
    Preserves topological execution order.
    """

    @staticmethod
    def aggregate(results: List[Dict[str, Any]], tasks: List[Task]) -> str:
        """
        Combines task results into a final cohesive response string.
        Since tasks execute in parallel, the results list might be out of order.
        We sort the results based on the original topological execution group and index.
        """
        if not results:
            return "No tasks were executed."

        if len(results) == 1:
            return results[0].get("result", "")

        # Map task IDs to their topological order
        task_order = {task.task_id: idx for idx, task in enumerate(tasks)}

        # Sort results based on the original topological order of tasks
        sorted_results = sorted(
            results, key=lambda r: task_order.get(r.get("task_id"), 999999)
        )

        aggregated_parts = []
        for r in sorted_results:
            agent = r.get("agent_used", "Unknown Agent")
            res_text = r.get("result", "")

            # Filter out internal orchestration and runtime logs
            if (
                "Delegated execution to Workflow Runtime" in res_text
                or "formulated Workflow" in res_text
            ):
                continue

            # Formatting clean up
            aggregated_parts.append(f"**{agent}**\n{res_text}")

        if not aggregated_parts:
            return "Workflow completed successfully, but returned no human-readable output."

        return "\n\n---\n\n".join(aggregated_parts)
