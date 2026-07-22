"""Tests for local function-backed tools."""

import asyncio
from collections.abc import Mapping

import pytest

from app.tools import FunctionTool, ToolCall, ToolDefinition, ToolError, ToolResult


def definition() -> ToolDefinition:
    """Create the definition shared by function tool tests."""
    return ToolDefinition(name="echo", description="Echo supplied input")


def test_function_tool_preserves_constructor_dependencies() -> None:
    tool_definition = definition()

    def handler(arguments: Mapping[str, object]) -> ToolResult:
        return ToolResult(content=str(arguments["value"]))

    tool = FunctionTool(tool_definition, handler)

    assert tool.definition is tool_definition
    assert tool._handler is handler


def test_invoke_calls_handler_once_and_returns_original_result() -> None:
    calls: list[Mapping[str, object]] = []
    expected = ToolResult(content="result")

    def handler(arguments: Mapping[str, object]) -> ToolResult:
        calls.append(arguments)
        return expected

    tool = FunctionTool(definition(), handler)
    call = ToolCall(tool_name="echo", arguments={"value": "input"})

    result = asyncio.run(tool.invoke(call))

    assert result is expected
    assert calls == [call.arguments]
    assert calls[0] is call.arguments


def test_invoke_does_not_modify_call_or_arguments() -> None:
    original_arguments: dict[str, object] = {"value": "input"}
    call = ToolCall(tool_name="echo", arguments=original_arguments)

    def handler(arguments: Mapping[str, object]) -> ToolResult:
        assert dict(arguments) == {"value": "input"}
        return ToolResult(content="result")

    tool = FunctionTool(definition(), handler)

    asyncio.run(tool.invoke(call))

    assert call.tool_name == "echo"
    assert dict(call.arguments) == {"value": "input"}
    assert original_arguments == {"value": "input"}


def test_invoke_rejects_mismatched_tool_name_without_calling_handler() -> None:
    call_count = 0

    def handler(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal call_count
        call_count += 1
        return ToolResult(content="result")

    tool = FunctionTool(definition(), handler)

    with pytest.raises(ToolError, match="does not match"):
        asyncio.run(tool.invoke(ToolCall(tool_name="other", arguments={})))

    assert call_count == 0


def test_invoke_propagates_original_tool_error() -> None:
    expected = ToolError("tool failure")

    def handler(arguments: Mapping[str, object]) -> ToolResult:
        raise expected

    tool = FunctionTool(definition(), handler)

    with pytest.raises(ToolError) as captured:
        asyncio.run(tool.invoke(ToolCall(tool_name="echo", arguments={})))

    assert captured.value is expected
    assert captured.value.__cause__ is None


def test_invoke_converts_other_exceptions_and_preserves_cause() -> None:
    expected = ValueError("handler failure")

    def handler(arguments: Mapping[str, object]) -> ToolResult:
        raise expected

    tool = FunctionTool(definition(), handler)

    with pytest.raises(ToolError, match="handler failed") as captured:
        asyncio.run(tool.invoke(ToolCall(tool_name="echo", arguments={})))

    assert captured.value.__cause__ is expected
