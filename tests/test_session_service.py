"""Tests for session history management."""

import asyncio

from app.providers.models import Message
from app.session import InMemorySessionStore, Session, SessionService


def test_service_creates_and_saves_missing_session() -> None:
    store = InMemorySessionStore()
    service = SessionService(store)

    session = asyncio.run(service.get_or_create("session-1"))

    assert session == Session(session_id="session-1", messages=())
    assert asyncio.run(store.get("session-1")) is session


def test_service_returns_existing_session() -> None:
    store = InMemorySessionStore()
    existing = Session(session_id="session-1", messages=())
    asyncio.run(store.save(existing))

    session = asyncio.run(SessionService(store).get_or_create("session-1"))

    assert session is existing


def test_service_appends_without_mutating_old_session() -> None:
    store = InMemorySessionStore()
    old_message = Message(role="user", content="first")
    old_session = Session(session_id="session-1", messages=(old_message,))
    new_message = Message(role="assistant", content="second")
    asyncio.run(store.save(old_session))

    updated = asyncio.run(
        SessionService(store).append_messages("session-1", (new_message,))
    )

    assert old_session.messages == (old_message,)
    assert updated.messages == (old_message, new_message)
    assert updated.messages[0] is old_message
    assert updated.messages[1] is new_message


def test_service_explicitly_replaces_complete_session() -> None:
    store = InMemorySessionStore()
    service = SessionService(store)
    replacement = Session(session_id="session-1", messages=())

    asyncio.run(service.save_session(replacement))

    assert asyncio.run(store.get("session-1")) is replacement
