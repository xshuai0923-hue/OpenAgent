"""Data models for loaded text documents."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    """Represent one loaded text document and its source path."""

    content: str
    source: Path
