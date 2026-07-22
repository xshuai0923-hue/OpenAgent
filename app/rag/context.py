"""Data models for retrieval-augmented context."""

from dataclasses import dataclass

from app.documents.models import Chunk


@dataclass(frozen=True)
class RagContext:
    """Contain document chunks selected as prompt context."""

    chunks: list[Chunk]
