"""Tests for application-level chat orchestration."""

import asyncio
from pathlib import Path

import pytest

from app.chat import ChatRequest, ChatService, ChatServiceError
from app.documents import Chunk
from app.prompts import PromptBuilder, PromptBuilderError
from app.providers import (
    BaseProvider,
    GenerationRequest,
    GenerationResponse,
    ProviderError,
)
from app.providers.models import Message
from app.rag import RagContext, RagService, RagServiceError
from app.retrievers import RetrievalRequest


class RecordingPromptBuilder(PromptBuilder):
    """Build messages while recording prompt inputs."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def build(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
    ) -> list[Message]:
        self.calls.append((user_prompt, system_prompt))
        return super().build(user_prompt=user_prompt, system_prompt=system_prompt)


class FailingPromptBuilder(PromptBuilder):
    """Raise a prompt-builder error for conversion tests."""

    @staticmethod
    def build(user_prompt: str, system_prompt: str | None = None) -> list[Message]:
        raise PromptBuilderError("prompt failure")


class RecordingProvider(BaseProvider):
    """Return a configured response while recording generation requests."""

    def __init__(self, response: GenerationResponse) -> None:
        self.response = response
        self.requests: list[GenerationRequest] = []

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        self.requests.append(request)
        return self.response


class FailingProvider(BaseProvider):
    """Raise a provider error for conversion tests."""

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        raise ProviderError("provider failure")


class RecordingRagService(RagService):
    """Return configured context while recording retrieval requests."""

    def __init__(self, context: RagContext) -> None:
        self.context = context
        self.requests: list[RetrievalRequest] = []

    async def retrieve_context(self, request: RetrievalRequest) -> RagContext:
        self.requests.append(request)
        return self.context


class FailingRagService(RagService):
    """Raise a RAG service error for conversion tests."""

    def __init__(self) -> None:
        pass

    async def retrieve_context(self, request: RetrievalRequest) -> RagContext:
        raise RagServiceError("rag failure")


def test_chat_without_retrieval_calls_builder_and_provider_once() -> None:
    response = GenerationResponse(text="answer")
    provider = RecordingProvider(response)
    builder = RecordingPromptBuilder()
    service = ChatService(provider, builder)
    request = ChatRequest(user_prompt="question", system_prompt="system")

    result = asyncio.run(service.chat(request))

    assert result is response
    assert builder.calls == [("question", "system")]
    assert provider.requests == [
        GenerationRequest(
            messages=[
                Message(role="system", content="system"),
                Message(role="user", content="question"),
            ]
        )
    ]
    assert request == ChatRequest(user_prompt="question", system_prompt="system")


def test_chat_with_retrieval_uses_context_template_and_original_query() -> None:
    context_chunk = Chunk(content="context", source=Path("document.txt"), index=0)
    retrieval_request = RetrievalRequest(query="  original query  ", top_k=2)
    rag_service = RecordingRagService(RagContext(chunks=[context_chunk]))
    provider = RecordingProvider(GenerationResponse(text="answer"))
    builder = RecordingPromptBuilder()
    request = ChatRequest(
        user_prompt="question",
        retrieval_request=retrieval_request,
    )

    asyncio.run(ChatService(provider, builder, rag_service).chat(request))

    assert rag_service.requests == [retrieval_request]
    assert rag_service.requests[0] is retrieval_request
    assert builder.calls == [("Context:\ncontext\n\nQuestion:\nquestion", None)]
    assert len(provider.requests) == 1
    assert request.retrieval_request is retrieval_request


def test_chat_with_empty_context_uses_original_prompt() -> None:
    rag_service = RecordingRagService(RagContext(chunks=[]))
    builder = RecordingPromptBuilder()
    provider = RecordingProvider(GenerationResponse(text="answer"))

    asyncio.run(
        ChatService(provider, builder, rag_service).chat(
            ChatRequest(
                user_prompt="question",
                retrieval_request=RetrievalRequest(query="query"),
            )
        )
    )

    assert builder.calls == [("question", None)]


def test_chat_ignores_retrieval_when_rag_service_is_absent() -> None:
    builder = RecordingPromptBuilder()
    provider = RecordingProvider(GenerationResponse(text="answer"))

    asyncio.run(
        ChatService(provider, builder).chat(
            ChatRequest(
                user_prompt="question",
                retrieval_request=RetrievalRequest(query="query"),
            )
        )
    )

    assert builder.calls == [("question", None)]


def test_chat_converts_rag_service_error() -> None:
    service = ChatService(
        RecordingProvider(GenerationResponse(text="answer")),
        RecordingPromptBuilder(),
        FailingRagService(),
    )

    with pytest.raises(ChatServiceError, match="RAG context") as captured:
        asyncio.run(
            service.chat(
                ChatRequest(
                    user_prompt="question",
                    retrieval_request=RetrievalRequest(query="query"),
                )
            )
        )

    assert isinstance(captured.value.__cause__, RagServiceError)


def test_chat_converts_prompt_builder_error() -> None:
    service = ChatService(
        RecordingProvider(GenerationResponse(text="answer")),
        FailingPromptBuilder(),
    )

    with pytest.raises(ChatServiceError, match="Prompt construction") as captured:
        asyncio.run(service.chat(ChatRequest(user_prompt="question")))

    assert isinstance(captured.value.__cause__, PromptBuilderError)


def test_chat_converts_provider_error() -> None:
    service = ChatService(FailingProvider(), RecordingPromptBuilder())

    with pytest.raises(ChatServiceError, match="Chat provider") as captured:
        asyncio.run(service.chat(ChatRequest(user_prompt="question")))

    assert isinstance(captured.value.__cause__, ProviderError)
