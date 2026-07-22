"""Framework-independent tool exceptions."""

from app.core.exceptions import ApplicationError


class ToolError(ApplicationError):
    """Base exception for failures in the tool layer."""
