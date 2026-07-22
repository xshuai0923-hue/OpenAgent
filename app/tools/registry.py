"""Registry for externally managed tool instances."""

from app.tools.base import BaseTool
from app.tools.exceptions import ToolError
from app.tools.models import ToolDefinition


class ToolRegistryError(ToolError):
    """Base exception for tool registry operations."""


class ToolAlreadyRegisteredError(ToolRegistryError):
    """Raised when a tool name is already registered."""


class ToolNotFoundError(ToolRegistryError):
    """Raised when a requested tool name is not registered."""


class ToolRegistry:
    """Manage externally created tools by their unique names."""

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool under its definition name."""
        name = tool.definition.name
        if name in self._tools:
            raise ToolAlreadyRegisteredError(f"Tool already registered: {name}")
        self._tools[name] = tool

    def unregister(self, name: str) -> None:
        """Remove a registered tool by name."""
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool not found: {name}")
        del self._tools[name]

    def get(self, name: str) -> BaseTool:
        """Return a registered tool by name."""
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool not found: {name}")
        return self._tools[name]

    def contains(self, name: str) -> bool:
        """Return whether a tool name is registered."""
        return name in self._tools

    def list_tools(self) -> tuple[ToolDefinition, ...]:
        """Return tool definitions sorted by tool name."""
        return tuple(self._tools[name].definition for name in sorted(self._tools))
