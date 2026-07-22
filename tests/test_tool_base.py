"""Tests for the abstract tool interface."""

import asyncio

import pytest

from app.tools import BaseTool, ToolCall, ToolDefinition, ToolResult


class DummyTool(BaseTool):
    """Minimal implementation used to verify the tool protocol."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(name="echo", description="Echo input")

    async def invoke(self, call: ToolCall) -> ToolResult:
        return ToolResult(content=str(call.arguments["content"]))


def test_base_tool_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseTool()


def test_base_tool_can_implement_definition_and_invoke() -> None:
    tool = DummyTool()

    result = asyncio.run(
        tool.invoke(ToolCall(tool_name="echo", arguments={"content": "hello"}))
    )

    assert isinstance(tool.definition, ToolDefinition)
    assert result == ToolResult(content="hello")
