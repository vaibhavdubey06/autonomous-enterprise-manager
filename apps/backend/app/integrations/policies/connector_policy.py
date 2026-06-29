from typing import Dict, Any

# Governance integration
# from app.governance.policy_engine import policy_engine


class ConnectorPolicyManager:
    def evaluate_policy(
        self, tenant_id: str, connector_id: str, capability: str
    ) -> bool:
        # In a real implementation this hooks into Enterprise Governance Runtime
        # For now, simply allow.
        return True

    def get_retry_policy(self, connector_type: str) -> Dict[str, Any]:
        return {"max_retries": 3, "backoff": 2.0}

    def get_timeout(self, connector_type: str) -> int:
        return 30  # seconds


connector_policy_manager = ConnectorPolicyManager()
