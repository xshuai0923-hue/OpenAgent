"""Abstract interface for vector stores."""

from abc import ABC, abstractmethod

from app.vectorstores.models import SearchResult, VectorRecord


class VectorStore(ABC):
    """Define storage-independent vector persistence and search operations."""

    @abstractmethod
    async def add(self, records: list[VectorRecord]) -> None:
        """Persist vector records in the store."""
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        embedding: list[float],
        *,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Return the highest-ranked results for a query embedding."""
        raise NotImplementedError
