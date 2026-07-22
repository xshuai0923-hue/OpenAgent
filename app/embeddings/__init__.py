"""Public interfaces for embedding providers."""

from app.embeddings.base import EmbeddingProvider
from app.embeddings.config import EmbeddingProviderConfig
from app.embeddings.exceptions import EmbeddingError
from app.embeddings.models import EmbeddingRequest, EmbeddingResponse
from app.embeddings.openai import OpenAIEmbeddingProvider

__all__ = [
    "EmbeddingError",
    "EmbeddingProvider",
    "EmbeddingProviderConfig",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "OpenAIEmbeddingProvider",
]
