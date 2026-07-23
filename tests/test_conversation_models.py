"""Tests for the conversation message container."""

from dataclasses import FrozenInstanceError

import pytest

from app.conversation import Conversation, ToolMessage
from app.providers.models import Message


def test_conversation_defaults_to_empty_tuple() -> None:
    conversation = Conversation()

    assert conversation.messages == ()
    assert isinstance(conversation.messages, tuple)
    assert conversation.to_provider_messages() == []


def test_conversation_preserves_multiple_messages_and_order() -> None:
    system = Message(role="system", content="instructions")
    user = Message(role="user", content="question")
    assistant = Message(role="assistant", content="answer")
    tool = ToolMessage(content="result", tool_call_id="call_123")

    conversation = Conversation(messages=(system, user, assistant, tool))

    assert conversation.messages == (system, user, assistant, tool)
    assert conversation.messages[0] is system
    assert conversation.messages[1] is user
    assert conversation.messages[2] is assistant
    assert conversation.messages[3] is tool


def test_conversation_defensively_converts_list_to_tuple() -> None:
    message = Message(role="user", content="question")
    messages = [message]

    conversation = Conversation(messages=messages)  # type: ignore[arg-type]
    messages.clear()

    assert conversation.messages == (message,)
    assert conversation.messages[0] is message


def test_conversation_is_frozen() -> None:
    conversation = Conversation()

    with pytest.raises(FrozenInstanceError):
        conversation.messages = ()


def test_to_provider_messages_returns_original_objects_in_order() -> None:
    user = Message(role="user", content="question")
    tool = ToolMessage(content="result", tool_call_id="call_123")
    conversation = Conversation(messages=(user, tool))

    messages = conversation.to_provider_messages()

    assert messages == [
        user,
        Message(role="tool", content="result", tool_call_id="call_123"),
    ]
    assert messages[0] is user
    assert messages[1].role == "tool"
    assert messages[1].tool_call_id == "call_123"
    messages.clear()
    assert conversation.messages == (user, tool)
