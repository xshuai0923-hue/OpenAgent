"""Application-level chat data models."""

from dataclasses import dataclass

from app.chat.exceptions import ChatServiceError
from app.retrievers.models import RetrievalRequest
from app.tools.models import ToolDefinition


@dataclass(frozen=True)
class ChatRequest:
    """Contain prompts and an optional retrieval request for one chat turn."""

    user_prompt: str
    system_prompt: str | None = None
    retrieval_request: RetrievalRequest | None = None
    tools: tuple[ToolDefinition, ...] = ()

    def __post_init__(self) -> None:
        """Reject blank user prompts while preserving the original value."""
        if not self.user_prompt.strip():
            raise ChatServiceError("User prompt must not be empty")
        if self.tools is None:
            raise ChatServiceError("Chat request tools must not be None")
        object.__setattr__(self, "tools", tuple(self.tools))
