"""Framework-independent chat service exceptions."""

from app.core.exceptions import ApplicationError


class ChatServiceError(ApplicationError):
    """Raised when a chat request cannot be completed."""
