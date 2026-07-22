"""Loading of UTF-8 text documents from local files."""

from pathlib import Path

from app.documents.exceptions import DocumentLoaderError
from app.documents.models import Document


class DocumentLoader:
    """Load complete UTF-8 text files without transforming their content."""

    @staticmethod
    def load(path: Path) -> Document:
        """Read one UTF-8 text file and return its original content."""
        if not path.exists():
            raise DocumentLoaderError("Document does not exist")
        if not path.is_file():
            raise DocumentLoaderError("Document path is not a regular file")

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise DocumentLoaderError("Document is not valid UTF-8") from error
        except OSError as error:
            raise DocumentLoaderError("Document could not be read") from error

        if not content.strip():
            raise DocumentLoaderError("Document is empty")

        return Document(content=content, source=path)
