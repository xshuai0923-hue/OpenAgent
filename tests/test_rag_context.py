"""Tests for retrieval-augmented context models."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.documents import Chunk
from app.rag import RagContext


def test_rag_context_preserves_chunk_objects() -> None:
    chunk = Chunk(content="context", source=Path("document.txt"), index=0)

    context = RagContext(chunks=[chunk])

    assert context.chunks == [chunk]
    assert context.chunks[0] is chunk


def test_rag_context_allows_empty_chunks() -> None:
    assert RagContext(chunks=[]).chunks == []


def test_rag_context_is_frozen() -> None:
    context = RagContext(chunks=[])

    with pytest.raises(FrozenInstanceError):
        context.chunks = []
