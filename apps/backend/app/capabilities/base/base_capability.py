from abc import ABC, abstractmethod
from typing import Dict, Any
import time
import logging

from app.capabilities.base.schemas import Capability, CapabilityResult

logger = logging.getLogger(__name__)


class BaseCapability(ABC):
    """
    Abstract base class for all Enterprise Capabilities.
    Enforces a strict execution lifecycle:
    authorize -> validate_input -> execute -> validate_output
    """

    @abstractmethod
    def get_metadata(self) -> Capability:
        """Returns the Capability metadata."""
        pass

    def validate_input(self, action: str, kwargs: Dict[str, Any]) -> bool:
        """
        Validates the input parameters for a given action.
        """
        metadata = self.get_metadata()
        if action not in metadata.supported_actions:
            raise ValueError(f"Action '{action}' is not supported by {metadata.name}.")
        return True

    def authorize(self, agent_name: str) -> bool:
        """
        Checks if the requesting agent is authorized to use this capability.
        """
        metadata = self.get_metadata()
        if (
            agent_name not in metadata.supported_agents
            and "*" not in metadata.supported_agents
        ):
            raise PermissionError(
                f"Agent '{agent_name}' is not authorized to use {metadata.name}."
            )
        return True

    @abstractmethod
    def _execute_internal(self, action: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        The actual implementation of the capability.
        Must be implemented by subclasses.
        """
        pass

    def validate_output(self, result: Dict[str, Any]) -> bool:
        """
        Validates the output of the execution.
        """
        return True

    def handle_errors(self, e: Exception) -> CapabilityResult:
        """
        Standardized error handling.
        """
        logger.error(f"Capability Error [{self.get_metadata().name}]: {e}")
        return CapabilityResult(
            success=False,
            capability_name=self.get_metadata().name,
            action="unknown",
            status="FAILED",
            errors=[str(e)],
        )

    def execute(self, agent_name: str, action: str, **kwargs) -> CapabilityResult:
        """
        The main entrypoint for executing a capability.
        Executes the full capability lifecycle.
        """
        start_time = time.time()
        metadata = self.get_metadata()
        logs = []

        try:
            logs.append(f"Authorizing {agent_name}...")
            self.authorize(agent_name)

            logs.append(f"Validating input for {action}...")
            self.validate_input(action, kwargs)

            logs.append(f"Executing {action}...")
            data = self._execute_internal(action, kwargs)

            logs.append("Validating output...")
            self.validate_output(data)

            execution_time = (time.time() - start_time) * 1000

            return CapabilityResult(
                success=True,
                capability_name=metadata.name,
                action=action,
                status="COMPLETED",
                execution_time_ms=execution_time,
                logs=logs,
                data=data,
            )

        except Exception as e:
            result = self.handle_errors(e)
            result.action = action
            result.execution_time_ms = (time.time() - start_time) * 1000
            result.logs = logs
            return result
