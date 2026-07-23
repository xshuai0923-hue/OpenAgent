"""Default application runtime implementation."""

from app.agents.exceptions import AgentLoopError
from app.agents.loop import AgentLoop
from app.chat.exceptions import ChatServiceError
from app.chat.models import ChatRequest
from app.chat.service import ChatService
from app.retrievers.models import RetrievalRequest
from app.runtime.base import BaseRuntime
from app.runtime.exceptions import RuntimeError
from app.runtime.models import RuntimeRequest, RuntimeResponse
from app.runtime.tool_runtime import _execute_tool_calls
from app.tools.exceptions import ToolError
from app.tools.executor import ToolExecutor


class DefaultAgentRuntime(BaseRuntime):
    """Run one chat request through an externally managed chat service."""

    def __init__(
        self,
        chat_service: ChatService,
        tool_executor: ToolExecutor | None = None,
        agent_loop: AgentLoop | None = None,
    ) -> None:
        """Store externally managed chat, tool, and agent dependencies."""
        self._chat_service = chat_service
        self._tool_executor = tool_executor
        self._agent_loop = agent_loop

    async def run(self, request: RuntimeRequest) -> RuntimeResponse:
        """Map a runtime request to chat and return its generated text."""
        retrieval_request = (
            RetrievalRequest(query=request.user_prompt) if request.enable_rag else None
        )
        chat_request = ChatRequest(
            user_prompt=request.user_prompt,
            system_prompt=request.system_prompt,
            retrieval_request=retrieval_request,
        )

        if self._agent_loop is not None:
            try:
                result = await self._agent_loop.run(chat_request)
            except AgentLoopError as error:
                raise RuntimeError("Agent runtime failed") from error
            return RuntimeResponse(response=result.response)

        try:
            generation = await self._chat_service.chat(chat_request)
        except ChatServiceError as error:
            raise RuntimeError("Chat runtime failed") from error

        if generation.tool_calls:
            if not request.enable_tools:
                raise RuntimeError("Tool execution is disabled for this request")
            if self._tool_executor is None:
                raise RuntimeError("Tool executor is required for tool calls")
            try:
                await _execute_tool_calls(
                    self._tool_executor,
                    generation.tool_calls,
                )
            except ToolError as error:
                raise RuntimeError("Runtime tool execution failed") from error

        return RuntimeResponse(response=generation.text)
