"""Conversation data models built from provider messages."""

from dataclasses import dataclass

from app.conversation.tool_message import ToolMessage
from app.providers.models import Message


@dataclass(frozen=True)
class Conversation:
    """Contain ordered provider messages without copying them."""

    messages: tuple[Message | ToolMessage, ...] = ()

    def __post_init__(self) -> None:
        """Isolate the ordered message collection as a tuple."""
        object.__setattr__(self, "messages", tuple(self.messages))

    def to_provider_messages(self) -> list[Message]:
        """Return ordered messages in provider-compatible list form."""
        return [
            (
                message.to_provider_message()
                if isinstance(message, ToolMessage)
                else message
            )
            for message in self.messages
        ]
