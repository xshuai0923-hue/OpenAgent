"""Tests for prompt message construction."""

import pytest

from app.prompts import PromptBuilder, PromptBuilderError
from app.providers.models import Message


def test_build_with_user_prompt_only() -> None:
    messages = PromptBuilder.build(user_prompt="Hello")

    assert messages == [Message(role="user", content="Hello")]
    assert isinstance(messages, list)


def test_build_with_system_and_user_prompts_preserves_order() -> None:
    messages = PromptBuilder.build(
        system_prompt="Be concise",
        user_prompt="Explain the result",
    )

    assert messages == [
        Message(role="system", content="Be concise"),
        Message(role="user", content="Explain the result"),
    ]


@pytest.mark.parametrize("system_prompt", [None, "", "   "])
def test_build_omits_empty_system_prompt(system_prompt: str | None) -> None:
    messages = PromptBuilder.build(
        system_prompt=system_prompt,
        user_prompt="Hello",
    )

    assert messages == [Message(role="user", content="Hello")]


@pytest.mark.parametrize("user_prompt", ["", "   "])
def test_build_rejects_empty_user_prompt(user_prompt: str) -> None:
    with pytest.raises(PromptBuilderError, match="User prompt"):
        PromptBuilder.build(user_prompt=user_prompt)


def test_build_does_not_add_assistant_message() -> None:
    messages = PromptBuilder.build(
        system_prompt="Be concise",
        user_prompt="Hello",
    )

    assert all(message.role != "assistant" for message in messages)
