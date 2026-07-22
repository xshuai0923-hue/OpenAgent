"""Tests for the vector store abstract interface."""

import asyncio
from pathlib import Path

import pytest

from app.documents import Chunk
from app.vectorstores import SearchResult, VectorRecord, VectorStore


class DummyVectorStore(VectorStore):
    """Minimal in-process implementation used to verify the interface."""

    def __init__(self) -> None:
        self.records: list[VectorRecord] = []

    async def add(self, records: list[VectorRecord]) -> None:
        self.records.extend(records)

    async def search(
        self,
        embedding: list[float],
        *,
        top_k: int = 5,
    ) -> list[SearchResult]:
        return [
            SearchResult(chunk=record.chunk, score=1.0)
            for record in self.records[:top_k]
        ]


def test_vector_store_is_abstract() -> None:
    with pytest.raises(TypeError):
        VectorStore()


def test_vector_store_can_be_implemented() -> None:
    store = DummyVectorStore()
    chunk = Chunk(content="content", source=Path("document.txt"), index=0)
    record = VectorRecord(chunk=chunk, embedding=[0.1, 0.2])

    async def exercise_store() -> list[SearchResult]:
        await store.add([record])
        return await store.search([0.1, 0.2])

    results = asyncio.run(exercise_store())

    assert isinstance(results, list)
    assert results == [SearchResult(chunk=chunk, score=1.0)]
