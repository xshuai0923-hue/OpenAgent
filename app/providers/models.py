"""Provider-independent generation data models."""

from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import urlparse

from app.providers.exceptions import ProviderError

MessageRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class Message:
    """Represent one validated message in a provider conversation."""

    role: MessageRole
    content: str

    def __post_init__(self) -> None:
        """Reject unsupported roles and empty message content."""
        if self.role not in {"system", "user", "assistant"}:
            raise ProviderError(f"Unsupported message role: {self.role!r}")
        if not self.content.strip():
            raise ProviderError("Message content must not be empty")


@dataclass(frozen=True)
class ProviderConfig:
    """Contain validated configuration for a provider instance."""

    api_key: str = field(repr=False)
    base_url: str
    model: str
    timeout: float

    def __post_init__(self) -> None:
        """Reject incomplete or invalid provider configuration."""
        if not self.api_key.strip():
            raise ProviderError("Provider API key must not be empty")
        if not self.base_url.strip():
            raise ProviderError("Provider base URL must not be empty")
        parsed_base_url = urlparse(self.base_url)
        if (
            parsed_base_url.scheme not in {"http", "https"}
            or not parsed_base_url.netloc
        ):
            raise ProviderError("Provider base URL must be a valid HTTP URL")
        if not self.model.strip():
            raise ProviderError("Provider model must not be empty")
        if self.timeout <= 0:
            raise ProviderError("Provider timeout must be greater than zero")


@dataclass(frozen=True)
class GenerationRequest:
    """Describe a provider-independent text generation request."""

    messages: list[Message]
    temperature: float = 0.7
    max_tokens: int = 1024

    def __post_init__(self) -> None:
        """Require at least one conversation message."""
        if not self.messages:
            raise ProviderError("Generation request requires at least one message")


@dataclass(frozen=True)
class GenerationResponse:
    """Contain provider-independent generated text."""

    text: str
