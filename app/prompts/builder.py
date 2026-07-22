"""Construction of provider-independent conversation messages."""

from app.core.exceptions import ApplicationError
from app.providers.models import Message


class PromptBuilderError(ApplicationError):
    """Raised when prompt input cannot produce valid messages."""


class PromptBuilder:
    """Build ordered conversation messages from prompt input."""

    @staticmethod
    def build(user_prompt: str, system_prompt: str | None = None) -> list[Message]:
        """Build an optional system message followed by one user message."""
        if not user_prompt.strip():
            raise PromptBuilderError("User prompt must not be empty")

        messages: list[Message] = []
        if system_prompt is not None and system_prompt.strip():
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=user_prompt))
        return messages
