"""Abstract interface for tools."""

from abc import ABC, abstractmethod

from app.tools.models import ToolCall, ToolDefinition, ToolResult


class BaseTool(ABC):
    """Define the common protocol implemented by tools."""

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return the tool's public definition."""
        raise NotImplementedError

    @abstractmethod
    async def invoke(self, call: ToolCall) -> ToolResult:
        """Invoke the tool for the supplied call."""
        raise NotImplementedError
