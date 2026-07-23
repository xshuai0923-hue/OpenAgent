"""Tests for provider-compatible tool result messages."""

from dataclasses import FrozenInstanceError

import pytest

from app.conversation import ToolMessage
from app.providers import ProviderError
from app.providers.models import Message


def test_tool_message_converts_without_losing_call_id() -> None:
    tool_message = ToolMessage(content="  result  ", tool_call_id="call_123")

    provider_message = tool_message.to_provider_message()

    assert tool_message.content == "  result  "
    assert tool_message.tool_call_id == "call_123"
    assert provider_message == Message(
        role="tool",
        content="  result  ",
        tool_call_id="call_123",
    )


@pytest.mark.parametrize(
    ("content", "tool_call_id"),
    [("", "call_123"), ("   ", "call_123"), ("result", ""), ("result", "   ")],
)
def test_tool_message_rejects_blank_fields(
    content: str,
    tool_call_id: str,
) -> None:
    with pytest.raises(ProviderError):
        ToolMessage(content=content, tool_call_id=tool_call_id)


def test_tool_message_is_frozen() -> None:
    message = ToolMessage(content="result", tool_call_id="call_123")

    with pytest.raises(FrozenInstanceError):
        message.content = "changed"
