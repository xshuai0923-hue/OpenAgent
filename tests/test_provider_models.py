"""Tests for provider-independent generation models."""

from dataclasses import FrozenInstanceError, fields

import pytest

from app.providers.exceptions import ProviderError
from app.providers.models import (
    GenerationRequest,
    GenerationResponse,
    Message,
    ProviderConfig,
)
from app.tools import ToolCall, ToolDefinition


def test_message_can_be_created() -> None:
    message = Message(role="system", content="Follow instructions")

    assert message.role == "system"
    assert message.content == "Follow instructions"


@pytest.mark.parametrize("role", ["system", "user", "assistant", "tool"])
def test_message_supports_conversation_roles(role: str) -> None:
    message = Message(
        role=role,  # type: ignore[arg-type]
        content="content",
        tool_call_id="call_123" if role == "tool" else "",
    )

    assert message.role == role


def test_message_validates_tool_call_id_by_role() -> None:
    assert Message(role="user", content="question").tool_call_id == ""
    tool_message = Message(
        role="tool",
        content="result",
        tool_call_id="call_123",
    )
    assert tool_message.tool_call_id == "call_123"

    with pytest.raises(ProviderError, match="requires a tool call ID"):
        Message(role="tool", content="result")
    with pytest.raises(ProviderError, match="Only tool messages"):
        Message(role="assistant", content="answer", tool_call_id="call_123")


def test_assistant_message_supports_tool_calls_and_empty_content() -> None:
    call = ToolCall(tool_name="search", arguments={}, call_id="call_123")
    calls = [call]

    message = Message(
        role="assistant",
        content="",
        tool_calls=calls,  # type: ignore[arg-type]
    )
    calls.clear()

    assert message.tool_calls == (call,)
    with pytest.raises(ProviderError, match="Only assistant"):
        Message(role="user", content="question", tool_calls=(call,))


def test_message_rejects_invalid_role() -> None:
    with pytest.raises(ProviderError, match="Unsupported message role"):
        Message(role="developer", content="result")  # type: ignore[arg-type]


def test_message_rejects_empty_content() -> None:
    with pytest.raises(ProviderError, match="content"):
        Message(role="user", content=" ")


def test_message_is_frozen() -> None:
    message = Message(role="assistant", content="hello")

    with pytest.raises(FrozenInstanceError):
        message.content = "changed"


def test_provider_config_validates_required_values() -> None:
    with pytest.raises(ProviderError, match="API key"):
        ProviderConfig(
            api_key=" ", base_url="https://example.com", model="model", timeout=1
        )
    with pytest.raises(ProviderError, match="base URL"):
        ProviderConfig(api_key="key", base_url=" ", model="model", timeout=1)
    with pytest.raises(ProviderError, match="valid HTTP URL"):
        ProviderConfig(api_key="key", base_url="not-a-url", model="model", timeout=1)
    with pytest.raises(ProviderError, match="model"):
        ProviderConfig(
            api_key="key", base_url="https://example.com", model=" ", timeout=1
        )
    with pytest.raises(ProviderError, match="timeout"):
        ProviderConfig(
            api_key="key",
            base_url="https://example.com",
            model="model",
            timeout=0,
        )


def test_provider_config_hides_api_key_from_repr() -> None:
    config = ProviderConfig(
        api_key="secret",
        base_url="https://example.com",
        model="model",
        timeout=30,
    )

    assert "secret" not in repr(config)


def test_generation_request_defaults() -> None:
    messages = [Message(role="user", content="hello")]
    request = GenerationRequest(messages=messages)

    assert request.messages == messages
    assert request.temperature == 0.7
    assert request.max_tokens == 1024
    assert request.tools == ()


def test_generation_request_rejects_empty_messages() -> None:
    with pytest.raises(ProviderError, match="at least one message"):
        GenerationRequest(messages=[])


def test_generation_models_are_frozen() -> None:
    request = GenerationRequest(messages=[Message(role="user", content="hello")])
    response = GenerationResponse(text="world")

    with pytest.raises(FrozenInstanceError):
        request.messages = []
    with pytest.raises(FrozenInstanceError):
        response.text = "changed"


def test_generation_models_support_immutable_tool_contracts() -> None:
    definition = ToolDefinition(name="search", description="Search documents")
    definitions = [definition]
    request = GenerationRequest(
        messages=[Message(role="user", content="hello")],
        tools=definitions,  # type: ignore[arg-type]
    )
    call = ToolCall(tool_name="search", arguments={"query": "hello"})
    calls = [call]
    response = GenerationResponse(
        text="using search",
        tool_calls=calls,  # type: ignore[arg-type]
    )

    definitions.clear()
    calls.clear()

    assert request.tools == (definition,)
    assert response.tool_calls == (call,)
    with pytest.raises(FrozenInstanceError):
        request.tools = ()
    with pytest.raises(FrozenInstanceError):
        response.tool_calls = ()


def test_generation_model_field_types() -> None:
    request_types = {field.name: field.type for field in fields(GenerationRequest)}
    response_types = {field.name: field.type for field in fields(GenerationResponse)}

    assert request_types == {
        "messages": list[Message],
        "temperature": float,
        "max_tokens": int,
        "tools": tuple[ToolDefinition, ...],
    }
    assert response_types == {
        "text": str,
        "tool_calls": tuple[ToolCall, ...],
    }
