"""Application service for session history ownership."""

from app.providers.models import Message
from app.session.models import Session
from app.session.store import SessionStore


class SessionService:
    """Create, load, append, and replace immutable sessions."""

    def __init__(self, store: SessionStore) -> None:
        """Store the externally managed session store."""
        self._store = store

    async def get_or_create(self, session_id: str) -> Session:
        """Return an existing session or create and save an empty one."""
        session = await self._store.get(session_id)
        if session is not None:
            return session
        session = Session(session_id=session_id, messages=())
        await self._store.save(session)
        return session

    async def append_messages(
        self,
        session_id: str,
        messages: tuple[Message, ...],
    ) -> Session:
        """Append messages by replacing the existing immutable session."""
        session = await self.get_or_create(session_id)
        updated = Session(
            session_id=session_id,
            messages=session.messages + messages,
        )
        await self._store.save(updated)
        return updated

    async def save_session(self, session: Session) -> None:
        """Replace the complete stored session without appending history."""
        await self._store.save(session)
