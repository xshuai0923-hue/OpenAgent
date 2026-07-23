"""Tests for one-stage tool execution in the default runtime."""

import asyncio

import pytest

from app.chat import ChatRequest, ChatService
from app.providers import GenerationResponse
from app.runtime import (
    DefaultAgentRuntime,
    RuntimeError,
    RuntimeRequest,
    RuntimeResponse,
)
from app.tools import ToolCall, ToolError, ToolExecutor, ToolResult


class RecordingChatService(ChatService):
    """Return a configured generation while recording requests."""

    def __init__(self, response: GenerationResponse) -> None:
        self.response = response
        self.requests: list[ChatRequest] = []

    async def chat(self, request: ChatRequest) -> GenerationResponse:
        self.requests.append(request)
        return self.response


class RecordingToolExecutor(ToolExecutor):
    """Record ordered tool calls and return successful results."""

    def __init__(self) -> None:
        self.calls: list[ToolCall] = []
        self.close_count = 0

    async def execute(self, call: ToolCall) -> ToolResult:
        self.calls.append(call)
        return ToolResult(content=f"executed {call.tool_name}")

    def close(self) -> None:
        """Record unexpected lifecycle management."""
        self.close_count += 1


class FailingToolExecutor(ToolExecutor):
    """Raise a configured tool error."""

    def __init__(self, error: ToolError) -> None:
        self.error = error
        self.calls: list[ToolCall] = []

    async def execute(self, call: ToolCall) -> ToolResult:
        self.calls.append(call)
        raise self.error


def runtime_request(*, enable_tools: bool) -> RuntimeRequest:
    """Create a runtime request with the requested tool capability."""
    return RuntimeRequest(
        user_prompt="question",
        system_prompt=None,
        enable_rag=False,
        enable_tools=enable_tools,
    )


def test_run_without_tool_calls_does_not_invoke_executor() -> None:
    generation = GenerationResponse(text="answer")
    chat_service = RecordingChatService(generation)
    executor = RecordingToolExecutor()
    request = runtime_request(enable_tools=True)

    response = asyncio.run(DefaultAgentRuntime(chat_service, executor).run(request))

    assert response == RuntimeResponse(response="answer")
    assert executor.calls == []
    assert chat_service.requests == [ChatRequest(user_prompt="question")]
    assert request == runtime_request(enable_tools=True)
    assert generation == GenerationResponse(text="answer")


def test_run_executes_one_tool_call_and_returns_original_text() -> None:
    tool_call = ToolCall(tool_name="search", arguments={"query": "question"})
    generation = GenerationResponse(text="tool requested", tool_calls=(tool_call,))
    executor = RecordingToolExecutor()

    response = asyncio.run(
        DefaultAgentRuntime(RecordingChatService(generation), executor).run(
            runtime_request(enable_tools=True)
        )
    )

    assert executor.calls == [tool_call]
    assert executor.calls[0] is tool_call
    assert response == RuntimeResponse(response="tool requested")
    assert generation.tool_calls == (tool_call,)
    assert executor.close_count == 0


def test_run_executes_multiple_tool_calls_in_order() -> None:
    first = ToolCall(tool_name="first", arguments={})
    second = ToolCall(tool_name="second", arguments={})
    executor = RecordingToolExecutor()
    generation = GenerationResponse(
        text="tools requested",
        tool_calls=(first, second),
    )

    asyncio.run(
        DefaultAgentRuntime(RecordingChatService(generation), executor).run(
            runtime_request(enable_tools=True)
        )
    )

    assert executor.calls == [first, second]
    assert executor.calls[0] is first
    assert executor.calls[1] is second


def test_run_rejects_tool_calls_when_tools_are_disabled() -> None:
    tool_call = ToolCall(tool_name="search", arguments={})
    executor = RecordingToolExecutor()
    runtime = DefaultAgentRuntime(
        RecordingChatService(
            GenerationResponse(text="tool requested", tool_calls=(tool_call,))
        ),
        executor,
    )

    with pytest.raises(RuntimeError, match="disabled"):
        asyncio.run(runtime.run(runtime_request(enable_tools=False)))

    assert executor.calls == []


def test_run_requires_executor_when_response_contains_tool_calls() -> None:
    tool_call = ToolCall(tool_name="search", arguments={})
    runtime = DefaultAgentRuntime(
        RecordingChatService(
            GenerationResponse(text="tool requested", tool_calls=(tool_call,))
        )
    )

    with pytest.raises(RuntimeError, match="executor is required"):
        asyncio.run(runtime.run(runtime_request(enable_tools=True)))


def test_run_converts_tool_error_and_preserves_cause() -> None:
    tool_call = ToolCall(tool_name="search", arguments={})
    expected = ToolError("tool failure")
    executor = FailingToolExecutor(expected)
    runtime = DefaultAgentRuntime(
        RecordingChatService(
            GenerationResponse(text="tool requested", tool_calls=(tool_call,))
        ),
        executor,
    )

    with pytest.raises(RuntimeError, match="tool execution failed") as captured:
        asyncio.run(runtime.run(runtime_request(enable_tools=True)))

    assert captured.value.__cause__ is expected
    assert executor.calls == [tool_call]
