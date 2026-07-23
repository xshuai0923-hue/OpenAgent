"""Tests for the default agent runtime."""

import asyncio

import pytest

from app.agents import AgentExecutionState, AgentLoop, AgentPhase, AgentResult
from app.chat import ChatRequest, ChatService, ChatServiceError
from app.providers import GenerationResponse
from app.providers.models import Message
from app.retrievers import RetrievalRequest
from app.runtime import (
    BaseRuntime,
    DefaultAgentRuntime,
    RuntimeError,
    RuntimeRequest,
    RuntimeResponse,
)


class RecordingChatService(ChatService):
    """Return a configured generation while recording chat requests."""

    def __init__(self, response: GenerationResponse) -> None:
        self.response = response
        self.requests: list[ChatRequest] = []

    async def chat(self, request: ChatRequest) -> GenerationResponse:
        self.requests.append(request)
        return self.response


class FailingChatService(ChatService):
    """Raise a configured chat service error."""

    def __init__(self, error: ChatServiceError) -> None:
        self.error = error
        self.call_count = 0

    async def chat(self, request: ChatRequest) -> GenerationResponse:
        self.call_count += 1
        raise self.error


class RecordingAgentLoop(AgentLoop):
    """Return a configured result while recording requests."""

    def __init__(self, result: AgentResult) -> None:
        self.result = result
        self.requests: list[ChatRequest] = []

    async def run(self, request: ChatRequest) -> AgentResult:
        self.requests.append(request)
        return self.result


def test_run_without_rag_maps_request_and_returns_response() -> None:
    generation = GenerationResponse(text="answer")
    chat_service = RecordingChatService(generation)
    runtime = DefaultAgentRuntime(chat_service)
    request = RuntimeRequest(
        user_prompt="  question  ",
        system_prompt="system",
        enable_rag=False,
        enable_tools=True,
    )

    response = asyncio.run(runtime.run(request))

    assert isinstance(runtime, BaseRuntime)
    assert runtime._chat_service is chat_service
    assert runtime._tool_executor is None
    assert runtime._agent_loop is None
    assert chat_service.requests == [
        ChatRequest(
            user_prompt="  question  ",
            system_prompt="system",
            retrieval_request=None,
        )
    ]
    assert len(chat_service.requests) == 1
    assert response == RuntimeResponse(response="answer")
    assert generation.text == "answer"
    assert request == RuntimeRequest(
        user_prompt="  question  ",
        system_prompt="system",
        enable_rag=False,
        enable_tools=True,
    )


def test_run_with_rag_uses_original_prompt_and_default_top_k() -> None:
    chat_service = RecordingChatService(GenerationResponse(text="answer"))
    request = RuntimeRequest(
        user_prompt="  original query  ",
        system_prompt=None,
        enable_rag=True,
        enable_tools=False,
    )

    asyncio.run(DefaultAgentRuntime(chat_service).run(request))

    assert chat_service.requests == [
        ChatRequest(
            user_prompt="  original query  ",
            system_prompt=None,
            retrieval_request=RetrievalRequest(query="  original query  "),
        )
    ]
    retrieval_request = chat_service.requests[0].retrieval_request
    assert retrieval_request is not None
    assert retrieval_request.query == request.user_prompt
    assert retrieval_request.top_k == 5


def test_run_does_not_cache_generation_response() -> None:
    chat_service = RecordingChatService(GenerationResponse(text="first"))
    runtime = DefaultAgentRuntime(chat_service)
    request = RuntimeRequest(
        user_prompt="question",
        system_prompt=None,
        enable_rag=False,
        enable_tools=False,
    )

    assert asyncio.run(runtime.run(request)) == RuntimeResponse(response="first")
    chat_service.response = GenerationResponse(text="second")
    assert asyncio.run(runtime.run(request)) == RuntimeResponse(response="second")
    assert len(chat_service.requests) == 2


def test_run_converts_chat_service_error_and_preserves_cause() -> None:
    expected = ChatServiceError("chat failure")
    chat_service = FailingChatService(expected)
    runtime = DefaultAgentRuntime(chat_service)
    request = RuntimeRequest(
        user_prompt="question",
        system_prompt=None,
        enable_rag=False,
        enable_tools=False,
    )

    with pytest.raises(RuntimeError, match="Chat runtime failed") as captured:
        asyncio.run(runtime.run(request))

    assert captured.value.__cause__ is expected
    assert chat_service.call_count == 1


def test_run_prioritizes_injected_agent_loop() -> None:
    chat_service = RecordingChatService(GenerationResponse(text="unused"))
    agent_loop = RecordingAgentLoop(
        AgentResult(
            response="agent answer",
            messages=(Message(role="assistant", content="agent answer"),),
            final_state=AgentExecutionState(
                phase=AgentPhase.FINISHED,
                messages=(Message(role="assistant", content="agent answer"),),
                iteration=1,
            ),
        )
    )
    runtime = DefaultAgentRuntime(chat_service, agent_loop=agent_loop)
    request = RuntimeRequest(
        user_prompt="question",
        system_prompt=None,
        enable_rag=False,
        enable_tools=True,
    )

    response = asyncio.run(runtime.run(request))

    assert response == RuntimeResponse(response="agent answer")
    assert agent_loop.requests == [ChatRequest(user_prompt="question")]
    assert chat_service.requests == []
