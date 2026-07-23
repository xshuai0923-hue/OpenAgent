"""Execution entry point for registered tools."""

from app.tools.exceptions import ToolError
from app.tools.models import ToolCall, ToolResult
from app.tools.registry import ToolRegistry, ToolRegistryError


class ToolExecutor:
    """Resolve and invoke tools registered in an external registry."""

    def __init__(self, registry: ToolRegistry) -> None:
        """Store the externally managed registry reference."""
        self._registry = registry

    async def execute(self, call: ToolCall) -> ToolResult:
        """Resolve one tool and return its invocation result unchanged."""
        try:
            tool = self._registry.get(call.tool_name)
        except ToolRegistryError as error:
            raise ToolError("Tool lookup failed") from error
        except Exception as error:
            raise ToolError("Tool lookup failed") from error

        try:
            return await tool.invoke(call)
        except ToolError:
            raise
        except Exception as error:
            raise ToolError("Tool execution failed") from error
