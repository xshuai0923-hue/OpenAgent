"""Abstract interface for embedding providers."""

from abc import ABC, abstractmethod

from app.embeddings.models import EmbeddingRequest, EmbeddingResponse


class EmbeddingProvider(ABC):
    """Define the common interface implemented by embedding providers."""

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Create embedding vectors for the supplied texts."""
        raise NotImplementedError
