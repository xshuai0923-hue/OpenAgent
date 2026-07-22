"""Provider-independent embedding data models."""

from dataclasses import dataclass

from app.embeddings.exceptions import EmbeddingError


@dataclass(frozen=True)
class EmbeddingRequest:
    """Contain non-empty texts to embed in their original order."""

    texts: list[str]

    def __post_init__(self) -> None:
        """Reject empty requests and blank text values."""
        if not self.texts:
            raise EmbeddingError("Embedding request requires at least one text")
        if any(not text.strip() for text in self.texts):
            raise EmbeddingError("Embedding request texts must not be empty")


@dataclass(frozen=True)
class EmbeddingResponse:
    """Contain non-empty embedding vectors in request order."""

    embeddings: list[list[float]]

    def __post_init__(self) -> None:
        """Reject empty responses and empty embedding vectors."""
        if not self.embeddings:
            raise EmbeddingError("Embedding response requires at least one embedding")
        if any(not embedding for embedding in self.embeddings):
            raise EmbeddingError("Embedding vectors must not be empty")
