"""Application-level chat data models."""

from dataclasses import dataclass

from app.chat.exceptions import ChatServiceError
from app.retrievers.models import RetrievalRequest


@dataclass(frozen=True)
class ChatRequest:
    """Contain prompts and an optional retrieval request for one chat turn."""

    user_prompt: str
    system_prompt: str | None = None
    retrieval_request: RetrievalRequest | None = None

    def __post_init__(self) -> None:
        """Reject blank user prompts while preserving the original value."""
        if not self.user_prompt.strip():
            raise ChatServiceError("User prompt must not be empty")
