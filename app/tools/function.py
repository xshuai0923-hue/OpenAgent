"""Tool implementation backed by a local Python function."""

from collections.abc import Callable, Mapping

from app.tools.base import BaseTool
from app.tools.exceptions import ToolError
from app.tools.models import ToolCall, ToolDefinition, ToolResult


class FunctionTool(BaseTool):
    """Adapt a synchronous local handler to the tool protocol."""

    def __init__(
        self,
        definition: ToolDefinition,
        handler: Callable[[Mapping[str, object]], ToolResult],
    ) -> None:
        """Store externally managed definition and handler references."""
        self._definition = definition
        self._handler = handler

    @property
    def definition(self) -> ToolDefinition:
        """Return the original tool definition."""
        return self._definition

    async def invoke(self, call: ToolCall) -> ToolResult:
        """Validate and invoke the local handler exactly once."""
        if call.tool_name != self._definition.name:
            raise ToolError(
                f"Tool call name {call.tool_name!r} does not match "
                f"{self._definition.name!r}"
            )

        try:
            return self._handler(call.arguments)
        except ToolError:
            raise
        except Exception as error:
            raise ToolError("Function tool handler failed") from error
