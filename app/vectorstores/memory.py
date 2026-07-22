"""In-memory vector storage with exact cosine similarity search."""

import math

from app.vectorstores.base import VectorStore
from app.vectorstores.exceptions import VectorStoreError
from app.vectorstores.models import SearchResult, VectorRecord


class InMemoryVectorStore(VectorStore):
    """Store vector records in insertion order for exact in-memory search."""

    def __init__(self) -> None:
        """Initialize an empty vector record collection."""
        self._records: list[VectorRecord] = []

    async def add(self, records: list[VectorRecord]) -> None:
        """Validate and append records without deduplication."""
        validated_records: list[VectorRecord] = []
        for record in records:
            self._magnitude(record.embedding, label="Stored embedding")
            validated_records.append(
                VectorRecord(
                    chunk=record.chunk,
                    embedding=list(record.embedding),
                )
            )
        self._records.extend(validated_records)

    async def search(
        self,
        embedding: list[float],
        *,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Return records ranked by exact cosine similarity."""
        if top_k <= 0:
            raise VectorStoreError("top_k must be greater than zero")
        query_magnitude = self._magnitude(embedding, label="Query embedding")

        results: list[SearchResult] = []
        for record in self._records:
            if len(record.embedding) != len(embedding):
                raise VectorStoreError("Embedding dimensions do not match")
            record_magnitude = self._magnitude(
                record.embedding,
                label="Stored embedding",
            )
            dot_product = sum(
                query_value * record_value
                for query_value, record_value in zip(embedding, record.embedding)
            )
            score = float(dot_product / (query_magnitude * record_magnitude))
            results.append(SearchResult(chunk=record.chunk, score=score))

        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]

    @staticmethod
    def _magnitude(embedding: list[float], *, label: str) -> float:
        if not embedding:
            raise VectorStoreError(f"{label} must not be empty")
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in embedding
        ):
            raise VectorStoreError(f"{label} must contain numbers")
        if any(not math.isfinite(value) for value in embedding):
            raise VectorStoreError(f"{label} must contain finite numbers")

        magnitude = math.sqrt(sum(value * value for value in embedding))
        if magnitude == 0:
            raise VectorStoreError(f"{label} must not be a zero vector")
        return magnitude
