"""Framework-independent RAG service exceptions."""

from app.core.exceptions import ApplicationError


class RagServiceError(ApplicationError):
    """Raised when retrieval-augmented context construction fails."""
