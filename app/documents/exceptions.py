"""Framework-independent document loading exceptions."""

from app.core.exceptions import ApplicationError


class DocumentLoaderError(ApplicationError):
    """Raised when a text document cannot be loaded."""
