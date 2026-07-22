"""Framework-independent vector store exceptions."""

from app.core.exceptions import ApplicationError


class VectorStoreError(ApplicationError):
    """Raised when vector store input or output is invalid."""
