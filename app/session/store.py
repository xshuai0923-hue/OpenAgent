"""Session storage contracts and in-memory implementation."""

from abc import ABC, abstractmethod

from app.session.models import Session


class SessionStore(ABC):
    """Define storage operations required by the session service."""

    @abstractmethod
    async def get(self, session_id: str) -> Session | None:
        """Return a stored session or ``None`` when it does not exist."""
        raise NotImplementedError

    @abstractmethod
    async def save(self, session: Session) -> None:
        """Replace the stored session for its identifier."""
        raise NotImplementedError


class InMemorySessionStore(SessionStore):
    """Store sessions in process memory without persistence."""

    def __init__(self) -> None:
        """Initialize empty process-local storage."""
        self._sessions: dict[str, Session] = {}

    async def get(self, session_id: str) -> Session | None:
        """Return the session stored for the supplied identifier."""
        return self._sessions.get(session_id)

    async def save(self, session: Session) -> None:
        """Replace the session stored for the supplied identifier."""
        self._sessions[session.session_id] = session
