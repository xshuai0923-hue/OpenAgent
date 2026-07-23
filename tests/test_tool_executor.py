"""Tests for registered tool execution."""

import asyncio

import pytest

from app.tools import (
    BaseTool,
    ToolCall,
    ToolDefinition,
    ToolError,
    ToolExecutor,
    ToolNotFoundError,
    ToolRegistry,
    ToolResult,
)


class TrackingTool(BaseTool):
    """Return configured results while recording invocations."""

    def __init__(self, result: ToolResult) -> None:
        self._definition = ToolDefinition(name="echo", description="Echo input")
        self.result = result
        self.calls: list[ToolCall] = []
        self.close_count = 0

    @property
    def definition(self) -> ToolDefinition:
        return self._definition

    async def invoke(self, call: ToolCall) -> ToolResult:
        self.calls.append(call)
        return self.result

    def close(self) -> None:
        """Record unexpected lifecycle management."""
        self.close_count += 1


class ToolErrorTool(TrackingTool):
    """Raise a configured tool error when invoked."""

    def __init__(self, error: ToolError) -> None:
        super().__init__(ToolResult(content="unused"))
        self.error = error

    async def invoke(self, call: ToolCall) -> ToolResult:
        self.calls.append(call)
        raise self.error


class FailingTool(TrackingTool):
    """Raise a non-tool exception when invoked."""

    def __init__(self, error: Exception) -> None:
        super().__init__(ToolResult(content="unused"))
        self.error = error

    async def invoke(self, call: ToolCall) -> ToolResult:
        self.calls.append(call)
        raise self.error


def registry_with(tool: BaseTool) -> ToolRegistry:
    """Create a registry containing one tool."""
    registry = ToolRegistry()
    registry.register(tool)
    return registry


def test_execute_invokes_tool_once_and_returns_original_result() -> None:
    expected = ToolResult(content="result")
    tool = TrackingTool(expected)
    registry = registry_with(tool)
    executor = ToolExecutor(registry)
    call = ToolCall(tool_name="echo", arguments={"value": "input"})

    result = asyncio.run(executor.execute(call))

    assert executor._registry is registry
    assert tool.calls == [call]
    assert tool.calls[0] is call
    assert result is expected
    assert registry.get("echo") is tool
    assert tool.close_count == 0


def test_execute_does_not_modify_call_or_result() -> None:
    expected = ToolResult(content="  original result  ")
    tool = TrackingTool(expected)
    call = ToolCall(tool_name="echo", arguments={"value": "input"})

    result = asyncio.run(ToolExecutor(registry_with(tool)).execute(call))

    assert call.tool_name == "echo"
    assert dict(call.arguments) == {"value": "input"}
    assert result is expected
    assert result.content == "  original result  "


def test_execute_does_not_cache_results() -> None:
    first = ToolResult(content="first")
    tool = TrackingTool(first)
    executor = ToolExecutor(registry_with(tool))
    call = ToolCall(tool_name="echo", arguments={})

    assert asyncio.run(executor.execute(call)) is first
    second = ToolResult(content="second")
    tool.result = second
    assert asyncio.run(executor.execute(call)) is second
    assert tool.calls == [call, call]


def test_execute_converts_missing_tool_error() -> None:
    executor = ToolExecutor(ToolRegistry())

    with pytest.raises(ToolError, match="lookup failed") as captured:
        asyncio.run(executor.execute(ToolCall(tool_name="missing", arguments={})))

    assert type(captured.value) is ToolError
    assert isinstance(captured.value.__cause__, ToolNotFoundError)


def test_execute_propagates_original_tool_error() -> None:
    expected = ToolError("tool failure")
    tool = ToolErrorTool(expected)

    with pytest.raises(ToolError) as captured:
        asyncio.run(
            ToolExecutor(registry_with(tool)).execute(
                ToolCall(tool_name="echo", arguments={})
            )
        )

    assert captured.value is expected
    assert len(tool.calls) == 1


def test_execute_converts_other_exception_and_preserves_cause() -> None:
    expected = RuntimeError("unexpected failure")
    tool = FailingTool(expected)

    with pytest.raises(ToolError, match="execution failed") as captured:
        asyncio.run(
            ToolExecutor(registry_with(tool)).execute(
                ToolCall(tool_name="echo", arguments={})
            )
        )

    assert captured.value.__cause__ is expected
    assert len(tool.calls) == 1
