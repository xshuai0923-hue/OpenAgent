"""Configuration for concrete embedding providers."""

from dataclasses import dataclass, field
from urllib.parse import urlparse

from app.embeddings.exceptions import EmbeddingError


@dataclass(frozen=True)
class EmbeddingProviderConfig:
    """Contain validated connection settings for an embedding provider."""

    api_key: str = field(repr=False)
    base_url: str
    model: str
    timeout: float

    def __post_init__(self) -> None:
        """Reject incomplete or invalid embedding provider configuration."""
        if not self.api_key.strip():
            raise EmbeddingError("Embedding provider API key must not be empty")
        if not self.base_url.strip():
            raise EmbeddingError("Embedding provider base URL must not be empty")
        parsed_base_url = urlparse(self.base_url)
        if (
            parsed_base_url.scheme not in {"http", "https"}
            or not parsed_base_url.netloc
        ):
            raise EmbeddingError("Embedding provider base URL must be a valid HTTP URL")
        if not self.model.strip():
            raise EmbeddingError("Embedding provider model must not be empty")
        if self.timeout <= 0:
            raise EmbeddingError("Embedding provider timeout must be greater than zero")
