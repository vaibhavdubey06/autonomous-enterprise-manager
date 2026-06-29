from app.governance.context.governance_context import GovernanceContext


class RiskEngine:
    """
    Calculates a dynamic risk score based on context.
    Returns: LOW, MEDIUM, HIGH, CRITICAL
    """

    def evaluate_risk(self, context: GovernanceContext) -> str:
        # Check target capability
        if context.capability_name in [
            "delete_database",
            "deploy_production",
            "drop_table",
        ]:
            return "CRITICAL"

        if context.capability_name in ["update_database", "modify_user_roles"]:
            return "HIGH"

        # Check goal content
        goal_lower = context.workflow_goal.lower()
        if "delete" in goal_lower or "drop" in goal_lower or "remove" in goal_lower:
            return "HIGH"

        if "budget" in goal_lower or "finance" in goal_lower or "cost" in goal_lower:
            return "MEDIUM"

        return "LOW"
