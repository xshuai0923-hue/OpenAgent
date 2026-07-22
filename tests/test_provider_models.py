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


def test_message_can_be_created() -> None:
    message = Message(role="system", content="Follow instructions")

    assert message.role == "system"
    assert message.content == "Follow instructions"


def test_message_rejects_invalid_role() -> None:
    with pytest.raises(ProviderError, match="Unsupported message role"):
        Message(role="tool", content="result")  # type: ignore[arg-type]


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


def test_generation_model_field_types() -> None:
    request_types = {field.name: field.type for field in fields(GenerationRequest)}
    response_types = {field.name: field.type for field in fields(GenerationResponse)}

    assert request_types == {
        "messages": list[Message],
        "temperature": float,
        "max_tokens": int,
    }
    assert response_types == {"text": str}
