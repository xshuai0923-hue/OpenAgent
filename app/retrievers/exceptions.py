"""Framework-independent retrieval exceptions."""

from app.core.exceptions import ApplicationError


class RetrieverError(ApplicationError):
    """Raised when retrieval input or output is invalid."""
