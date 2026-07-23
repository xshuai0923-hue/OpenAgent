"""Tests for tool definitions flowing through the chat contract."""

import asyncio

from app.chat import ChatRequest, ChatService
from app.prompts import PromptBuilder
from app.providers import BaseProvider, GenerationRequest, GenerationResponse
from app.tools import ToolDefinition


class RecordingProvider(BaseProvider):
    """Record generation requests without executing tools."""

    def __init__(self) -> None:
        self.requests: list[GenerationRequest] = []

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        self.requests.append(request)
        return GenerationResponse(text="answer")


def test_chat_service_passes_tools_without_executing_them() -> None:
    definition = ToolDefinition(name="search", description="Search documents")
    provider = RecordingProvider()
    request = ChatRequest(user_prompt="question", tools=(definition,))

    response = asyncio.run(ChatService(provider, PromptBuilder()).chat(request))

    assert response == GenerationResponse(text="answer")
    assert len(provider.requests) == 1
    assert provider.requests[0].tools == (definition,)
    assert provider.requests[0].tools[0] is definition
