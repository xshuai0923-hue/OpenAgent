"""Storage-independent vector data models."""

import math
from dataclasses import dataclass

from app.documents.models import Chunk
from app.vectorstores.exceptions import VectorStoreError


@dataclass(frozen=True)
class VectorRecord:
    """Associate one document chunk with its embedding vector."""

    chunk: Chunk
    embedding: list[float]

    def __post_init__(self) -> None:
        """Reject empty vectors and non-numeric vector values."""
        if not self.embedding:
            raise VectorStoreError("Vector record embedding must not be empty")
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in self.embedding
        ):
            raise VectorStoreError("Vector record embedding must contain numbers")


@dataclass(frozen=True)
class SearchResult:
    """Associate one matching chunk with a finite similarity score."""

    chunk: Chunk
    score: float

    def __post_init__(self) -> None:
        """Reject non-numeric and non-finite search scores."""
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise VectorStoreError("Search result score must be numeric")
        if not math.isfinite(self.score):
            raise VectorStoreError("Search result score must be finite")
