"""Provider-independent generation data models."""

from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import urlparse

from app.providers.exceptions import ProviderError
from app.tools.models import ToolCall, ToolDefinition

MessageRole = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class Message:
    """Represent one validated message in a provider conversation."""

    role: MessageRole
    content: str
    tool_call_id: str = ""
    tool_calls: tuple[ToolCall, ...] = ()

    def __post_init__(self) -> None:
        """Reject unsupported roles and empty message content."""
        if self.role not in {"system", "user", "assistant", "tool"}:
            raise ProviderError(f"Unsupported message role: {self.role!r}")
        if self.tool_calls is None:
            raise ProviderError("Message tool calls must not be None")
        object.__setattr__(self, "tool_calls", tuple(self.tool_calls))
        if not self.content.strip() and not (
            self.role == "assistant" and self.tool_calls
        ):
            raise ProviderError("Message content must not be empty")
        if self.role != "assistant" and self.tool_calls:
            raise ProviderError("Only assistant messages may include tool calls")
        if self.role == "tool" and not self.tool_call_id.strip():
            raise ProviderError("Tool message requires a tool call ID")
        if self.role != "tool" and self.tool_call_id:
            raise ProviderError("Only tool messages may include a tool call ID")


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
    tools: tuple[ToolDefinition, ...] = ()

    def __post_init__(self) -> None:
        """Require at least one conversation message."""
        if not self.messages:
            raise ProviderError("Generation request requires at least one message")
        if self.tools is None:
            raise ProviderError("Generation request tools must not be None")
        object.__setattr__(self, "tools", tuple(self.tools))


@dataclass(frozen=True)
class GenerationResponse:
    """Contain provider-independent generated text."""

    text: str
    tool_calls: tuple[ToolCall, ...] = ()

    def __post_init__(self) -> None:
        """Isolate the tool call tuple and reject absent collections."""
        if self.tool_calls is None:
            raise ProviderError("Generation response tool calls must not be None")
        object.__setattr__(self, "tool_calls", tuple(self.tool_calls))
