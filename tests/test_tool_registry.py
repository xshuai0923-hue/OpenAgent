"""Tests for tool instance registration and discovery."""

import pytest

from app.tools import (
    BaseTool,
    ToolAlreadyRegisteredError,
    ToolCall,
    ToolDefinition,
    ToolNotFoundError,
    ToolRegistry,
    ToolRegistryError,
    ToolResult,
)


class TrackingTool(BaseTool):
    """Expose lifecycle flags to verify registry boundaries."""

    def __init__(self, name: str) -> None:
        self._definition = ToolDefinition(name=name, description=f"Tool {name}")
        self.invoke_count = 0
        self.close_count = 0

    @property
    def definition(self) -> ToolDefinition:
        return self._definition

    async def invoke(self, call: ToolCall) -> ToolResult:
        self.invoke_count += 1
        return ToolResult(content="result")

    def close(self) -> None:
        """Record close attempts made by a registry under test."""
        self.close_count += 1


def test_register_and_get_preserve_tool_instance() -> None:
    registry = ToolRegistry()
    tool = TrackingTool("search")

    registry.register(tool)

    assert registry.get("search") is tool
    assert registry.contains("search") is True


def test_register_rejects_duplicate_name() -> None:
    registry = ToolRegistry()
    registry.register(TrackingTool("search"))

    with pytest.raises(ToolAlreadyRegisteredError, match="search") as captured:
        registry.register(TrackingTool("search"))

    assert isinstance(captured.value, ToolRegistryError)


def test_unregister_removes_tool_without_closing_it() -> None:
    registry = ToolRegistry()
    tool = TrackingTool("search")
    registry.register(tool)

    registry.unregister("search")

    assert registry.contains("search") is False
    assert tool.close_count == 0


def test_unregister_rejects_unknown_name_without_key_error() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolNotFoundError, match="missing") as captured:
        registry.unregister("missing")

    assert isinstance(captured.value, ToolRegistryError)
    assert captured.value.__cause__ is None


def test_get_rejects_unknown_name_without_key_error() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolNotFoundError, match="missing") as captured:
        registry.get("missing")

    assert isinstance(captured.value, ToolRegistryError)
    assert captured.value.__cause__ is None


def test_contains_returns_false_for_unknown_name() -> None:
    assert ToolRegistry().contains("missing") is False


def test_list_tools_returns_empty_tuple() -> None:
    definitions = ToolRegistry().list_tools()

    assert definitions == ()
    assert isinstance(definitions, tuple)


def test_list_tools_returns_definition_instead_of_tool() -> None:
    registry = ToolRegistry()
    tool = TrackingTool("search")
    registry.register(tool)

    definitions = registry.list_tools()

    assert definitions == (tool.definition,)
    assert definitions[0] is tool.definition
    assert not isinstance(definitions[0], BaseTool)


def test_list_tools_sorts_by_name_and_does_not_expose_registry_state() -> None:
    registry = ToolRegistry()
    beta = TrackingTool("beta")
    alpha = TrackingTool("alpha")
    registry.register(beta)
    registry.register(alpha)

    definitions = registry.list_tools()

    assert definitions == (alpha.definition, beta.definition)
    assert isinstance(definitions, tuple)
    assert registry.get("alpha") is alpha
    assert registry.get("beta") is beta


def test_registry_never_invokes_or_closes_tools() -> None:
    registry = ToolRegistry()
    tool = TrackingTool("search")

    registry.register(tool)
    registry.contains("search")
    registry.get("search")
    registry.list_tools()
    registry.unregister("search")

    assert tool.invoke_count == 0
    assert tool.close_count == 0
