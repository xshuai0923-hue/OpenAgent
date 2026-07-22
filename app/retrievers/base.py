"""Abstract interface for retrievers."""

from abc import ABC, abstractmethod

from app.retrievers.models import RetrievalRequest, RetrievalResult


class Retriever(ABC):
    """Define the common interface implemented by retrievers."""

    @abstractmethod
    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """Retrieve ranked results for the supplied query."""
        raise NotImplementedError
