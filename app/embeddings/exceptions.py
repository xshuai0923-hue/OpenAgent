"""Framework-independent embedding exceptions."""

from app.core.exceptions import ApplicationError


class EmbeddingError(ApplicationError):
    """Raised when embedding input or output is invalid."""
