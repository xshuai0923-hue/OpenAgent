"""Implementation-independent tool data models."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from app.tools.exceptions import ToolError


@dataclass(frozen=True)
class ToolParameter:
    """Describe one named input accepted by a tool."""

    name: str
    description: str
    required: bool = True

    def __post_init__(self) -> None:
        """Reject blank parameter names and descriptions."""
        if not self.name.strip():
            raise ToolError("Tool parameter name must not be empty")
        if not self.description.strip():
            raise ToolError("Tool parameter description must not be empty")


@dataclass(frozen=True)
class ToolDefinition:
    """Describe a tool and its ordered input parameters."""

    name: str
    description: str
    parameters: tuple[ToolParameter, ...] = ()

    def __post_init__(self) -> None:
        """Validate text fields and isolate the parameter tuple."""
        if not self.name.strip():
            raise ToolError("Tool name must not be empty")
        if not self.description.strip():
            raise ToolError("Tool description must not be empty")
        object.__setattr__(self, "parameters", tuple(self.parameters))


@dataclass(frozen=True)
class ToolCall:
    """Describe one immutable tool invocation request."""

    tool_name: str
    arguments: Mapping[str, object]

    def __post_init__(self) -> None:
        """Validate the tool name and defensively copy its arguments."""
        if not self.tool_name.strip():
            raise ToolError("Tool call name must not be empty")
        object.__setattr__(
            self,
            "arguments",
            MappingProxyType(dict(self.arguments)),
        )


@dataclass(frozen=True)
class ToolResult:
    """Contain the textual result returned by a tool."""

    content: str

    def __post_init__(self) -> None:
        """Reject empty tool result content."""
        if not self.content.strip():
            raise ToolError("Tool result content must not be empty")
