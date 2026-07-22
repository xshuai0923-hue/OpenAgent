"""Framework-independent provider exceptions."""

from app.core.exceptions import ApplicationError


class ProviderError(ApplicationError):
    """Raised when provider configuration or communication fails."""
