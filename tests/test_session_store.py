"""Tests for process-local session storage."""

import asyncio

from app.session import InMemorySessionStore, Session


def test_store_returns_none_for_missing_session() -> None:
    store = InMemorySessionStore()

    assert asyncio.run(store.get("missing")) is None


def test_store_saves_and_returns_same_session() -> None:
    store = InMemorySessionStore()
    session = Session(session_id="session-1", messages=())

    asyncio.run(store.save(session))

    assert asyncio.run(store.get("session-1")) is session


def test_store_replaces_existing_session() -> None:
    store = InMemorySessionStore()
    original = Session(session_id="session-1", messages=())
    replacement = Session(session_id="session-1", messages=())

    asyncio.run(store.save(original))
    asyncio.run(store.save(replacement))

    assert asyncio.run(store.get("session-1")) is replacement


def test_store_isolates_multiple_sessions() -> None:
    store = InMemorySessionStore()
    first = Session(session_id="first", messages=())
    second = Session(session_id="second", messages=())

    asyncio.run(store.save(first))
    asyncio.run(store.save(second))

    assert asyncio.run(store.get("first")) is first
    assert asyncio.run(store.get("second")) is second
