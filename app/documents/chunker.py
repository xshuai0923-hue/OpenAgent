"""Character-based splitting of loaded text documents."""

from app.core.exceptions import ApplicationError
from app.documents.models import Chunk, Document


class DocumentSplitterError(ApplicationError):
    """Raised when document splitting parameters are invalid."""


class DocumentSplitter:
    """Split documents into ordered, overlapping character chunks."""

    @staticmethod
    def split(
        document: Document,
        *,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> list[Chunk]:
        """Split a document with a fixed character size and overlap."""
        if chunk_size <= 0:
            raise DocumentSplitterError("Chunk size must be greater than zero")
        if chunk_overlap < 0:
            raise DocumentSplitterError("Chunk overlap must not be negative")
        if chunk_overlap >= chunk_size:
            raise DocumentSplitterError("Chunk overlap must be smaller than chunk size")

        chunks: list[Chunk] = []
        step = chunk_size - chunk_overlap
        for start in range(0, len(document.content), step):
            content = document.content[start : start + chunk_size]
            if not content:
                break
            chunks.append(
                Chunk(
                    content=content,
                    source=document.source,
                    index=len(chunks),
                )
            )
            if start + chunk_size >= len(document.content):
                break

        return chunks
