"""Tests for exact in-memory vector search."""

import asyncio
from pathlib import Path

import pytest

from app.documents import Chunk
from app.vectorstores import (
    InMemoryVectorStore,
    SearchResult,
    VectorRecord,
    VectorStoreError,
)


def record(index: int, embedding: list[float]) -> VectorRecord:
    return VectorRecord(
        chunk=Chunk(
            content=f"chunk-{index}",
            source=Path("document.txt"),
            index=index,
        ),
        embedding=embedding,
    )


def test_empty_store_returns_empty_results() -> None:
    store = InMemoryVectorStore()

    results = asyncio.run(store.search([1.0, 0.0]))

    assert results == []


def test_add_single_record_and_search() -> None:
    store = InMemoryVectorStore()
    item = record(0, [1.0, 0.0])

    async def exercise_store() -> list[SearchResult]:
        await store.add([item])
        return await store.search([1.0, 0.0])

    results = asyncio.run(exercise_store())

    assert results == [SearchResult(chunk=item.chunk, score=1.0)]


def test_add_multiple_records_preserves_order_for_equal_scores() -> None:
    store = InMemoryVectorStore()
    records = [record(0, [1.0, 0.0]), record(1, [2.0, 0.0])]

    async def exercise_store() -> list[SearchResult]:
        await store.add(records)
        return await store.search([1.0, 0.0])

    results = asyncio.run(exercise_store())

    assert [result.chunk for result in results] == [item.chunk for item in records]


def test_add_empty_list_does_not_change_store() -> None:
    store = InMemoryVectorStore()

    async def exercise_store() -> list[SearchResult]:
        await store.add([])
        return await store.search([1.0])

    assert asyncio.run(exercise_store()) == []


def test_search_sorts_by_cosine_similarity() -> None:
    store = InMemoryVectorStore()
    records = [
        record(0, [-1.0, 0.0]),
        record(1, [0.0, 1.0]),
        record(2, [1.0, 0.0]),
    ]

    async def exercise_store() -> list[SearchResult]:
        await store.add(records)
        return await store.search([1.0, 0.0])

    results = asyncio.run(exercise_store())

    assert [result.chunk.index for result in results] == [2, 1, 0]
    assert [result.score for result in results] == [1.0, 0.0, -1.0]


def test_search_respects_top_k() -> None:
    store = InMemoryVectorStore()
    records = [record(index, [1.0, float(index + 1)]) for index in range(3)]

    async def exercise_store() -> list[SearchResult]:
        await store.add(records)
        return await store.search([1.0, 0.0], top_k=2)

    assert len(asyncio.run(exercise_store())) == 2


def test_search_returns_all_records_when_top_k_is_larger() -> None:
    store = InMemoryVectorStore()
    records = [record(0, [1.0]), record(1, [2.0])]

    async def exercise_store() -> list[SearchResult]:
        await store.add(records)
        return await store.search([1.0], top_k=10)

    assert len(asyncio.run(exercise_store())) == 2


def test_search_rejects_dimension_mismatch() -> None:
    store = InMemoryVectorStore()

    async def exercise_store() -> None:
        await store.add([record(0, [1.0, 0.0])])
        await store.search([1.0])

    with pytest.raises(VectorStoreError, match="dimensions"):
        asyncio.run(exercise_store())


@pytest.mark.parametrize("embedding", [[], ["invalid"], [True]])
def test_search_rejects_invalid_query_embedding(embedding: list[object]) -> None:
    store = InMemoryVectorStore()

    with pytest.raises(VectorStoreError):
        asyncio.run(store.search(embedding))  # type: ignore[arg-type]


@pytest.mark.parametrize("embedding", [[0.0, 0.0], [float("nan")], [float("inf")]])
def test_search_rejects_zero_or_non_finite_query(embedding: list[float]) -> None:
    store = InMemoryVectorStore()

    with pytest.raises(VectorStoreError):
        asyncio.run(store.search(embedding))


@pytest.mark.parametrize("embedding", [[0.0, 0.0], [float("nan")], [float("inf")]])
def test_add_rejects_zero_or_non_finite_record(embedding: list[float]) -> None:
    store = InMemoryVectorStore()

    with pytest.raises(VectorStoreError):
        asyncio.run(store.add([record(0, embedding)]))


@pytest.mark.parametrize("top_k", [0, -1])
def test_search_rejects_non_positive_top_k(top_k: int) -> None:
    store = InMemoryVectorStore()

    with pytest.raises(VectorStoreError, match="top_k"):
        asyncio.run(store.search([1.0], top_k=top_k))


def test_repeated_search_is_consistent_and_does_not_modify_store() -> None:
    store = InMemoryVectorStore()
    records = [record(0, [1.0, 0.0]), record(1, [0.0, 1.0])]

    async def exercise_store() -> tuple[list[SearchResult], list[SearchResult]]:
        await store.add(records)
        first = await store.search([1.0, 0.0])
        second = await store.search([1.0, 0.0])
        return first, second

    first, second = asyncio.run(exercise_store())

    assert first == second
    assert len(first) == len(records)


def test_add_does_not_modify_or_retain_mutable_embedding() -> None:
    store = InMemoryVectorStore()
    embedding = [1.0, 0.0]
    item = record(0, embedding)

    asyncio.run(store.add([item]))
    embedding[0] = 0.0

    results = asyncio.run(store.search([1.0, 0.0]))
    assert results == [SearchResult(chunk=item.chunk, score=1.0)]
