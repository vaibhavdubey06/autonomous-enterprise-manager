import logging
import time
from app.capabilities.base.schemas import CapabilityResult
from app.capabilities.base.capability_registry import CapabilityRegistry

logger = logging.getLogger(__name__)


class CapabilityExecutor:
    """
    Executes Capabilities safely on behalf of Agents.
    Provides a central chokepoint for observability, error handling, and authorization.
    """

    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry

    def execute(
        self, agent_name: str, capability_id: str, action: str, **kwargs
    ) -> CapabilityResult:
        """
        Resolves the capability and executes the requested action.
        """
        start_time = time.time()
        logger.info(
            f"CapabilityExecutor: Agent '{agent_name}' requesting '{capability_id}.{action}'"
        )

        capability = self.registry.get(capability_id)
        if not capability:
            logger.error(f"Capability '{capability_id}' not found in registry.")
            return CapabilityResult(
                success=False,
                capability_name=capability_id,
                action=action,
                status="FAILED",
                execution_time_ms=(time.time() - start_time) * 1000,
                errors=[f"Capability '{capability_id}' not found."],
            )

        # The capability's own execute() method handles authorize, validate, execute, validate
        result = capability.execute(agent_name=agent_name, action=action, **kwargs)

        # Centralized observability
        if result.success:
            logger.info(
                f"Capability '{capability_id}.{action}' executed successfully in {result.execution_time_ms:.2f}ms"
            )
        else:
            logger.error(
                f"Capability '{capability_id}.{action}' failed: {result.errors}"
            )

        return result
