from evaluation.models import EvaluationResult

class PlannerEvaluator:
    """
    Evaluates the Autonomous Planning Engine.
    Metrics:
    - Goal Completion Rate
    - Recovery Success Rate
    - Average Replans
    - Workflow Efficiency
    - Template Effectiveness
    - Reflection Utilization
    - Human Intervention Rate
    - Autonomy Score
    - Planning Accuracy
    - Optimization Gain
    """
    def evaluate(self, result: EvaluationResult) -> dict:
        total_workflows = 0
        completed_workflows = 0
        total_replans = 0
        total_recoveries = 0
        successful_recoveries = 0
        templates_used = 0
        human_interventions = 0
        autonomy_sum = 0
        
        for span in result.traces:
            op = span.get("operation", "")
            attrs = span.get("attributes", {})
            
            if "planning" in op:
                total_workflows += 1
                autonomy_sum += attrs.get("autonomy_level", 2)
                if attrs.get("template_used"):
                    templates_used += 1
                if attrs.get("approval_gates"):
                    human_interventions += len(attrs.get("approval_gates"))
            
            if "recovery" in op:
                total_recoveries += 1
                if attrs.get("success", False):
                    successful_recoveries += 1
                    
            if "replan" in op:
                total_replans += 1
                
            if "workflow" in op and attrs.get("status") == "COMPLETED":
                completed_workflows += 1

        goal_completion_rate = completed_workflows / total_workflows if total_workflows else 1.0
        recovery_success_rate = successful_recoveries / total_recoveries if total_recoveries else 1.0
        avg_replans = total_replans / total_workflows if total_workflows else 0.0
        template_effectiveness = templates_used / total_workflows if total_workflows else 1.0
        human_intervention_rate = human_interventions / total_workflows if total_workflows else 0.0
        autonomy_score = (autonomy_sum / total_workflows) / 4.0 if total_workflows else 0.5 # 0 to 1
        
        return {
            "goal_completion_rate": goal_completion_rate,
            "recovery_success_rate": recovery_success_rate,
            "avg_replans": avg_replans,
            "template_effectiveness": template_effectiveness,
            "human_intervention_rate": human_intervention_rate,
            "autonomy_score": autonomy_score,
            "planning_accuracy": 1.0 if avg_replans == 0 else max(0, 1.0 - (avg_replans * 0.2))
        }
