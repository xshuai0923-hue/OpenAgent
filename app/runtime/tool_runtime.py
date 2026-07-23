"""Internal helpers for one-stage runtime tool execution."""

from app.tools.executor import ToolExecutor
from app.tools.models import ToolCall


async def _execute_tool_calls(
    executor: ToolExecutor,
    tool_calls: tuple[ToolCall, ...],
) -> None:
    """Execute tool calls sequentially in their original order."""
    for tool_call in tool_calls:
        await executor.execute(tool_call)
