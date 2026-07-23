"""Immutable session data models."""

from dataclasses import dataclass

from app.providers.models import Message
from app.session.exceptions import SessionError


@dataclass(frozen=True)
class Session:
    """Contain one session identifier and its ordered message history."""

    session_id: str
    messages: tuple[Message, ...]

    def __post_init__(self) -> None:
        """Validate the identifier and require immutable message storage."""
        if not isinstance(self.session_id, str) or not self.session_id:
            raise SessionError("Session ID must not be empty")
        if not isinstance(self.messages, tuple):
            raise SessionError("Session messages must be a tuple")
