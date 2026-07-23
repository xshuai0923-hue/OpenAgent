"""Tests for application-level chat models."""

from dataclasses import FrozenInstanceError

import pytest

from app.chat import ChatRequest, ChatServiceError
from app.retrievers import RetrievalRequest
from app.tools import ToolDefinition


def test_chat_request_preserves_values() -> None:
    retrieval_request = RetrievalRequest(query="query")
    request = ChatRequest(
        user_prompt="  user prompt  ",
        system_prompt="system prompt",
        retrieval_request=retrieval_request,
    )

    assert request.user_prompt == "  user prompt  "
    assert request.system_prompt == "system prompt"
    assert request.retrieval_request is retrieval_request
    assert request.tools == ()


def test_chat_request_defensively_copies_tools() -> None:
    definition = ToolDefinition(name="search", description="Search documents")
    tools = [definition]

    request = ChatRequest(user_prompt="question", tools=tools)  # type: ignore[arg-type]
    tools.clear()

    assert request.tools == (definition,)


@pytest.mark.parametrize("user_prompt", ["", "   "])
def test_chat_request_rejects_blank_user_prompt(user_prompt: str) -> None:
    with pytest.raises(ChatServiceError, match="User prompt"):
        ChatRequest(user_prompt=user_prompt)


def test_chat_request_is_frozen() -> None:
    request = ChatRequest(user_prompt="prompt")

    with pytest.raises(FrozenInstanceError):
        request.user_prompt = "changed"
