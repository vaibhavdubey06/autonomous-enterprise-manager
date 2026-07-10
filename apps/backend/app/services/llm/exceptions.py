class LLMError(Exception):
    """Base exception for all LLM-related errors."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when the provider times out."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when the provider rate limits the request."""

    pass


class LLMAuthenticationError(LLMError):
    """Raised when API credentials are invalid."""

    pass


class LLMValidationError(LLMError):
    """Exception raised when LLM structured output fails schema validation."""

    pass


class GuardrailException(LLMError):
    """Exception raised when a guardrail blocks a request or response."""

    def __init__(self, message: str, findings: list | None = None):
        super().__init__(message)
        self.findings = findings or []


class LLMProviderError(LLMError):
    """Raised when the provider returns an internal error."""

    pass
    """Raised when the response does not match the expected schema."""
    pass
