"""Tests for chat prompt formatting."""

from pathlib import Path

from app.chat import ChatPromptFormatter
from app.documents import Chunk
from app.rag import RagContext


def chunk(content: str, index: int) -> Chunk:
    """Create a context chunk for formatter tests."""
    return Chunk(content=content, source=Path("document.txt"), index=index)


def test_format_without_context_returns_original_prompt() -> None:
    prompt = "  original question  "

    assert ChatPromptFormatter.format(user_prompt=prompt, context=None) is prompt


def test_format_with_empty_context_returns_original_prompt() -> None:
    prompt = "question"

    result = ChatPromptFormatter.format(
        user_prompt=prompt,
        context=RagContext(chunks=[]),
    )

    assert result is prompt


def test_format_with_one_chunk_matches_public_template() -> None:
    result = ChatPromptFormatter.format(
        user_prompt="What is this?",
        context=RagContext(chunks=[chunk("First context", 0)]),
    )

    assert result == "Context:\nFirst context\n\nQuestion:\nWhat is this?"


def test_format_preserves_multiple_chunk_order_and_content() -> None:
    first = chunk(" first content ", 0)
    second = chunk("second\ncontent", 1)

    result = ChatPromptFormatter.format(
        user_prompt=" question ",
        context=RagContext(chunks=[first, second]),
    )

    assert result == (
        "Context:\n first content \n\nsecond\ncontent\n\nQuestion:\n question "
    )
    assert first.content == " first content "
    assert second.content == "second\ncontent"
