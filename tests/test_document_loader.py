"""Tests for UTF-8 text document loading."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.documents import Document, DocumentLoader, DocumentLoaderError


def test_document_contains_content_and_source() -> None:
    source = Path("document.txt")

    document = Document(content="content", source=source)

    assert document.content == "content"
    assert document.source == source


def test_document_is_frozen() -> None:
    document = Document(content="content", source=Path("document.txt"))

    with pytest.raises(FrozenInstanceError):
        document.content = "changed"


def test_load_reads_text_without_modification(tmp_path: Path) -> None:
    path = tmp_path / "document.txt"
    original_content = "  original content  \n"
    path.write_text(original_content, encoding="utf-8")

    document = DocumentLoader.load(path)

    assert document == Document(content=original_content, source=path)


def test_load_reads_utf8_chinese(tmp_path: Path) -> None:
    path = tmp_path / "chinese.txt"
    path.write_text("你好，世界", encoding="utf-8")

    document = DocumentLoader.load(path)

    assert document.content == "你好，世界"


def test_load_preserves_multiline_text(tmp_path: Path) -> None:
    path = tmp_path / "multiline.txt"
    content = "first line\nsecond line\nthird line"
    path.write_text(content, encoding="utf-8")

    document = DocumentLoader.load(path)

    assert document.content == content


def test_load_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(DocumentLoaderError, match="does not exist"):
        DocumentLoader.load(tmp_path / "missing.txt")


def test_load_rejects_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.txt"
    path.write_text("", encoding="utf-8")

    with pytest.raises(DocumentLoaderError, match="empty"):
        DocumentLoader.load(path)


def test_load_rejects_whitespace_file(tmp_path: Path) -> None:
    path = tmp_path / "whitespace.txt"
    path.write_text(" \n\t ", encoding="utf-8")

    with pytest.raises(DocumentLoaderError, match="empty"):
        DocumentLoader.load(path)


def test_load_rejects_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "invalid.txt"
    path.write_bytes(b"\xff\xfe")

    with pytest.raises(DocumentLoaderError, match="UTF-8"):
        DocumentLoader.load(path)


def test_load_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(DocumentLoaderError, match="regular file"):
        DocumentLoader.load(tmp_path)
