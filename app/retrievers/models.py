"""Implementation-independent retrieval data models."""

from dataclasses import dataclass

from app.retrievers.exceptions import RetrieverError
from app.vectorstores.models import SearchResult


@dataclass(frozen=True)
class RetrievalRequest:
    """Contain a non-empty query and requested result limit."""

    query: str
    top_k: int = 5

    def __post_init__(self) -> None:
        """Reject blank queries and non-positive result limits."""
        if not self.query.strip():
            raise RetrieverError("Retrieval query must not be empty")
        if self.top_k <= 0:
            raise RetrieverError("Retrieval top_k must be greater than zero")


@dataclass(frozen=True)
class RetrievalResult:
    """Contain search results returned by a retriever."""

    results: list[SearchResult]
