"""Tests for implementation-independent tool models."""

from dataclasses import FrozenInstanceError

import pytest

from app.tools import ToolCall, ToolDefinition, ToolError, ToolParameter, ToolResult


def test_tool_parameter_preserves_values_and_defaults() -> None:
    parameter = ToolParameter(name="  query  ", description="  Search query  ")

    assert parameter.name == "  query  "
    assert parameter.description == "  Search query  "
    assert parameter.required is True


@pytest.mark.parametrize(
    ("field", "value"),
    [("name", ""), ("name", "   "), ("description", ""), ("description", "   ")],
)
def test_tool_parameter_rejects_blank_text(field: str, value: str) -> None:
    values = {"name": "query", "description": "Search query", field: value}

    with pytest.raises(ToolError, match=field):
        ToolParameter(**values)


def test_tool_parameter_is_frozen() -> None:
    parameter = ToolParameter(name="query", description="Search query")

    with pytest.raises(FrozenInstanceError):
        parameter.name = "changed"


def test_tool_definition_preserves_values_and_parameters() -> None:
    parameter = ToolParameter(name="query", description="Search query")
    definition = ToolDefinition(
        name="  search  ",
        description="  Search documents  ",
        parameters=(parameter,),
    )

    assert definition.name == "  search  "
    assert definition.description == "  Search documents  "
    assert definition.parameters == (parameter,)


def test_tool_definition_defaults_to_empty_parameter_tuple() -> None:
    definition = ToolDefinition(name="search", description="Search documents")

    assert definition.parameters == ()
    assert isinstance(definition.parameters, tuple)


@pytest.mark.parametrize(
    ("field", "value"),
    [("name", ""), ("name", "   "), ("description", ""), ("description", "   ")],
)
def test_tool_definition_rejects_blank_text(field: str, value: str) -> None:
    values = {"name": "search", "description": "Search documents", field: value}

    with pytest.raises(ToolError, match=field):
        ToolDefinition(**values)


def test_tool_definition_is_frozen() -> None:
    definition = ToolDefinition(name="search", description="Search documents")

    with pytest.raises(FrozenInstanceError):
        definition.name = "changed"


def test_tool_call_defensively_copies_arguments() -> None:
    arguments: dict[str, object] = {"query": "original"}
    call = ToolCall(tool_name="  search  ", arguments=arguments)

    arguments["query"] = "changed"
    arguments["new"] = True

    assert call.tool_name == "  search  "
    assert call.call_id == ""
    assert dict(call.arguments) == {"query": "original"}
    with pytest.raises(TypeError):
        call.arguments["query"] = "changed"  # type: ignore[index]


def test_tool_call_preserves_custom_call_id() -> None:
    call = ToolCall(tool_name="search", arguments={}, call_id="call_123")

    assert call.call_id == "call_123"
    with pytest.raises(FrozenInstanceError):
        call.call_id = "changed"


@pytest.mark.parametrize("tool_name", ["", "   "])
def test_tool_call_rejects_blank_name(tool_name: str) -> None:
    with pytest.raises(ToolError, match="name"):
        ToolCall(tool_name=tool_name, arguments={})


def test_tool_call_is_frozen() -> None:
    call = ToolCall(tool_name="search", arguments={})

    with pytest.raises(FrozenInstanceError):
        call.tool_name = "changed"


def test_tool_result_preserves_content() -> None:
    result = ToolResult(content="  result  ")

    assert result.content == "  result  "


@pytest.mark.parametrize("content", ["", "   "])
def test_tool_result_rejects_blank_content(content: str) -> None:
    with pytest.raises(ToolError, match="content"):
        ToolResult(content=content)


def test_tool_result_is_frozen() -> None:
    result = ToolResult(content="result")

    with pytest.raises(FrozenInstanceError):
        result.content = "changed"
