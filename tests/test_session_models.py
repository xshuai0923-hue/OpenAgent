"""Tests for immutable session models."""

from dataclasses import FrozenInstanceError

import pytest

from app.providers.models import Message
from app.session import Session, SessionError


def test_session_preserves_identifier_messages_and_identity() -> None:
    message = Message(role="user", content="question")
    messages = (message,)

    session = Session(session_id="  session-1  ", messages=messages)

    assert session.session_id == "  session-1  "
    assert session.messages is messages
    assert session.messages[0] is message


def test_session_rejects_empty_identifier() -> None:
    with pytest.raises(SessionError, match="ID"):
        Session(session_id="", messages=())


def test_session_requires_tuple_messages() -> None:
    with pytest.raises(SessionError, match="tuple"):
        Session(session_id="session-1", messages=[])


def test_session_is_frozen() -> None:
    session = Session(session_id="session-1", messages=())

    with pytest.raises(FrozenInstanceError):
        session.session_id = "session-2"
