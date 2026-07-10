from evaluation.models import EvaluationResult


class SupervisorEvaluator:
    def evaluate(self, result: EvaluationResult) -> dict:
        planner_quality = 0.0
        tool_accuracy = 0.0

        used_tools = set()
        for span in result.traces:
            # Look for tool execution spans or planner decisions
            op = span.get("operation", "")
            if "tool" in op.lower() or "action" in op.lower():
                tool_name = span.get("attributes", {}).get("tool_name", "")
                if tool_name:
                    used_tools.add(tool_name)

        expected_tools = set(result.expected_tools)
        if expected_tools:
            overlap = len(used_tools.intersection(expected_tools))
            tool_accuracy = overlap / len(expected_tools)
            planner_quality = tool_accuracy
        else:
            # If no tools expected, and none used -> perfect
            if not used_tools:
                tool_accuracy = 1.0
                planner_quality = 1.0

        return {
            "planner_quality": planner_quality,
            "tool_selection_accuracy": tool_accuracy,
        }
