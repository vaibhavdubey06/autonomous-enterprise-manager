class AutonomousEnterpriseError(Exception):
    """Base exception for the entire application."""

    pass


class WorkflowExecutionError(AutonomousEnterpriseError):
    """Raised when a workflow execution fails."""

    pass


class CapabilityExecutionError(AutonomousEnterpriseError):
    """Raised when a capability fails to execute."""

    pass


class DatabaseConnectionError(AutonomousEnterpriseError):
    """Raised when a database connection fails."""

    pass


class AuthenticationError(AutonomousEnterpriseError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(AutonomousEnterpriseError):
    """Raised when authorization fails."""

    pass


class ResourceNotFoundError(AutonomousEnterpriseError):
    """Raised when a requested resource is not found."""

    pass
