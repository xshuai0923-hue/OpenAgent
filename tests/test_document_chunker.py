"""Tests for character-based document splitting."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.documents import Chunk, Document, DocumentSplitter, DocumentSplitterError


def test_chunk_contains_expected_fields() -> None:
    source = Path("document.txt")

    chunk = Chunk(content="content", source=source, index=0)

    assert chunk.content == "content"
    assert chunk.source == source
    assert chunk.index == 0


def test_chunk_is_frozen() -> None:
    chunk = Chunk(content="content", source=Path("document.txt"), index=0)

    with pytest.raises(FrozenInstanceError):
        chunk.content = "changed"


def test_split_short_document_returns_one_chunk() -> None:
    document = Document(content="short", source=Path("document.txt"))

    chunks = DocumentSplitter.split(document, chunk_size=10, chunk_overlap=2)

    assert chunks == [Chunk(content="short", source=document.source, index=0)]


def test_split_document_into_multiple_chunks_without_overlap() -> None:
    document = Document(content="abcdefghij", source=Path("document.txt"))

    chunks = DocumentSplitter.split(document, chunk_size=4, chunk_overlap=0)

    assert [chunk.content for chunk in chunks] == ["abcd", "efgh", "ij"]
    assert [chunk.index for chunk in chunks] == [0, 1, 2]


def test_split_applies_overlap_and_preserves_order() -> None:
    document = Document(content="abcdefghij", source=Path("document.txt"))

    chunks = DocumentSplitter.split(document, chunk_size=4, chunk_overlap=1)

    assert [chunk.content for chunk in chunks] == ["abcd", "defg", "ghij"]


def test_split_respects_chunk_size_and_source() -> None:
    source = Path("document.txt")
    document = Document(content="abcdefghijk", source=source)

    chunks = DocumentSplitter.split(document, chunk_size=5, chunk_overlap=2)

    assert all(0 < len(chunk.content) <= 5 for chunk in chunks)
    assert all(chunk.source == source for chunk in chunks)


def test_split_empty_document_returns_no_chunks() -> None:
    document = Document(content="", source=Path("document.txt"))

    assert DocumentSplitter.split(document) == []


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_split_rejects_non_positive_chunk_size(chunk_size: int) -> None:
    document = Document(content="content", source=Path("document.txt"))

    with pytest.raises(DocumentSplitterError, match="greater than zero"):
        DocumentSplitter.split(document, chunk_size=chunk_size)


def test_split_rejects_negative_overlap() -> None:
    document = Document(content="content", source=Path("document.txt"))

    with pytest.raises(DocumentSplitterError, match="not be negative"):
        DocumentSplitter.split(document, chunk_overlap=-1)


@pytest.mark.parametrize("chunk_overlap", [4, 5])
def test_split_rejects_overlap_not_smaller_than_size(chunk_overlap: int) -> None:
    document = Document(content="content", source=Path("document.txt"))

    with pytest.raises(DocumentSplitterError, match="smaller than chunk size"):
        DocumentSplitter.split(
            document,
            chunk_size=4,
            chunk_overlap=chunk_overlap,
        )


def test_split_does_not_modify_document() -> None:
    document = Document(content="abcdefghij", source=Path("document.txt"))
    original = Document(content=document.content, source=document.source)

    DocumentSplitter.split(document, chunk_size=4, chunk_overlap=1)

    assert document == original
