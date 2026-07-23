"""Framework-independent runtime exceptions."""

from app.core.exceptions import ApplicationError


class RuntimeError(ApplicationError):
    """Base exception for failures in the runtime layer."""
