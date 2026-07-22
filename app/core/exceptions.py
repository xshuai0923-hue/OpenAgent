"""Framework-independent application exceptions."""


class ApplicationError(Exception):
    """Base exception for application-level failures."""


class ConfigurationError(ApplicationError):
    """Raised when application configuration is invalid."""
