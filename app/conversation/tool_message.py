"""Conversation message for returning a tool result."""

from dataclasses import dataclass

from app.providers.exceptions import ProviderError
from app.providers.models import Message


@dataclass(frozen=True)
class ToolMessage:
    """Associate non-empty tool result content with its tool call."""

    content: str
    tool_call_id: str

    def __post_init__(self) -> None:
        """Reject content or call identifiers that cannot form a message."""
        if not self.content.strip():
            raise ProviderError("Tool message content must not be empty")
        if not self.tool_call_id.strip():
            raise ProviderError("Tool message call ID must not be empty")

    def to_provider_message(self) -> Message:
        """Return the equivalent provider tool message."""
        return Message(
            role="tool",
            content=self.content,
            tool_call_id=self.tool_call_id,
        )
