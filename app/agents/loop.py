"""Bounded tool-calling agent loop."""

from app.agents.exceptions import AgentLoopError
from app.agents.models import AgentExecutionState, AgentResult
from app.agents.state import AgentPhase
from app.agents.state_machine import AgentStateMachine
from app.chat.exceptions import ChatServiceError
from app.chat.models import ChatRequest
from app.chat.service import ChatService
from app.conversation import Conversation, ToolMessage
from app.providers.exceptions import ProviderError
from app.providers.models import Message
from app.session.exceptions import SessionError
from app.session.models import Session
from app.session.service import SessionService
from app.tools.exceptions import ToolError
from app.tools.executor import ToolExecutor
from app.tools.models import ToolDefinition


class AgentLoop:
    """Coordinate bounded chat and sequential tool execution."""

    def __init__(
        self,
        chat_service: ChatService,
        tool_executor: ToolExecutor,
        tools: tuple[ToolDefinition, ...],
        max_iterations: int = 5,
        *,
        session_service: SessionService | None = None,
        session_id: str | None = None,
    ) -> None:
        """Store external dependencies and validate the provider call limit."""
        if max_iterations <= 0:
            raise AgentLoopError("max_iterations must be greater than zero")
        if session_id == "":
            raise AgentLoopError("Session ID must not be empty")
        if session_service is not None and session_id is None:
            raise AgentLoopError(
                "Session ID is required when session service is configured"
            )
        self._chat_service = chat_service
        self._tool_executor = tool_executor
        self._tools = tuple(tools)
        self._max_iterations = max_iterations
        self._session_service = session_service
        self._session_id = session_id

    async def run(self, request: ChatRequest) -> AgentResult:
        """Run chat and tools until a final answer or the call limit."""
        self._state_machine = AgentStateMachine(
            AgentExecutionState(
                phase=AgentPhase.INIT,
                messages=(),
                iteration=0,
            )
        )
        try:
            session_messages: tuple[Message, ...] = ()
            if self._session_service is not None:
                try:
                    session = await self._session_service.get_or_create(
                        self._session_id
                    )
                except SessionError as error:
                    raise AgentLoopError("Agent session loading failed") from error
                session_messages = session.messages

            try:
                initial_messages = await self._chat_service.build_messages(request)
            except ChatServiceError as error:
                raise AgentLoopError("Agent message construction failed") from error

            conversation = Conversation(
                messages=session_messages + tuple(initial_messages)
            )
            self._state_machine.transition(
                AgentPhase.THINKING,
                messages=tuple(conversation.to_provider_messages()),
            )
            for _ in range(self._max_iterations):
                try:
                    generation = await self._chat_service.chat_messages(
                        conversation.to_provider_messages(),
                        tools=self._tools,
                    )
                except ChatServiceError as error:
                    raise AgentLoopError("Agent chat failed") from error

                iteration = self._state_machine.state.iteration + 1
                try:
                    assistant_message = Message(
                        role="assistant",
                        content=generation.text,
                        tool_calls=generation.tool_calls,
                    )
                except ProviderError as error:
                    raise AgentLoopError(
                        "Agent received an invalid response"
                    ) from error

                conversation = Conversation(
                    messages=conversation.messages + (assistant_message,)
                )
                provider_messages = tuple(conversation.to_provider_messages())
                if not generation.tool_calls:
                    if self._session_service is not None:
                        try:
                            await self._session_service.save_session(
                                Session(
                                    session_id=self._session_id,
                                    messages=provider_messages,
                                )
                            )
                        except SessionError as error:
                            raise AgentLoopError(
                                "Agent session saving failed"
                            ) from error
                    self._state_machine.transition(
                        AgentPhase.FINISHED,
                        messages=provider_messages,
                        iteration=iteration,
                    )
                    return AgentResult(
                        response=generation.text,
                        messages=provider_messages,
                        final_state=self._state_machine.state,
                    )

                self._state_machine.transition(
                    AgentPhase.TOOL_EXECUTION,
                    messages=provider_messages,
                    iteration=iteration,
                )
                tool_messages: list[ToolMessage] = []
                for tool_call in generation.tool_calls:
                    if not tool_call.call_id.strip():
                        raise AgentLoopError("Tool call ID must not be empty")
                    try:
                        result = await self._tool_executor.execute(tool_call)
                        content = result.content
                    except ToolError as error:
                        content = str(error).strip() or "Tool execution failed"
                    tool_messages.append(
                        ToolMessage(
                            content=content,
                            tool_call_id=tool_call.call_id,
                        )
                    )

                conversation = Conversation(
                    messages=conversation.messages + tuple(tool_messages)
                )
                self._state_machine.transition(
                    AgentPhase.OBSERVATION,
                    messages=tuple(conversation.to_provider_messages()),
                )
                self._state_machine.transition(AgentPhase.THINKING)

            raise AgentLoopError("Agent exceeded maximum provider calls")
        except Exception:
            if self._state_machine.state.phase not in {
                AgentPhase.FINISHED,
                AgentPhase.FAILED,
            }:
                self._state_machine.transition(AgentPhase.FAILED)
            raise
