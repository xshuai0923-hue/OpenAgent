"""Tests for storage-independent vector models."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.documents import Chunk
from app.vectorstores import SearchResult, VectorRecord, VectorStoreError


@pytest.fixture
def chunk() -> Chunk:
    return Chunk(content="content", source=Path("document.txt"), index=0)


def test_vector_record_can_be_created(chunk: Chunk) -> None:
    record = VectorRecord(chunk=chunk, embedding=[0.1, 0.2])

    assert record.chunk == chunk
    assert record.embedding == [0.1, 0.2]


def test_vector_record_rejects_empty_embedding(chunk: Chunk) -> None:
    with pytest.raises(VectorStoreError, match="must not be empty"):
        VectorRecord(chunk=chunk, embedding=[])


@pytest.mark.parametrize("value", ["invalid", True])
def test_vector_record_rejects_non_numeric_embedding(
    chunk: Chunk,
    value: object,
) -> None:
    with pytest.raises(VectorStoreError, match="contain numbers"):
        VectorRecord(chunk=chunk, embedding=[value])  # type: ignore[list-item]


def test_vector_record_is_frozen(chunk: Chunk) -> None:
    record = VectorRecord(chunk=chunk, embedding=[0.1])

    with pytest.raises(FrozenInstanceError):
        record.embedding = []


def test_search_result_can_be_created(chunk: Chunk) -> None:
    result = SearchResult(chunk=chunk, score=0.9)

    assert result.chunk == chunk
    assert result.score == 0.9


def test_search_result_rejects_nan_score(chunk: Chunk) -> None:
    with pytest.raises(VectorStoreError, match="finite"):
        SearchResult(chunk=chunk, score=float("nan"))


@pytest.mark.parametrize("score", [float("inf"), float("-inf")])
def test_search_result_rejects_infinite_score(chunk: Chunk, score: float) -> None:
    with pytest.raises(VectorStoreError, match="finite"):
        SearchResult(chunk=chunk, score=score)


def test_search_result_is_frozen(chunk: Chunk) -> None:
    result = SearchResult(chunk=chunk, score=0.9)

    with pytest.raises(FrozenInstanceError):
        result.score = 0.5
