"""Tests for the bounded tool-calling agent loop."""

import asyncio

import pytest

from app.agents import (
    AgentExecutionState,
    AgentLoop,
    AgentLoopError,
    AgentPhase,
    AgentResult,
    AgentStateMachine,
)
from app.chat import ChatRequest, ChatService
from app.providers import GenerationResponse
from app.providers.models import Message
from app.session import (
    InMemorySessionStore,
    Session,
    SessionError,
    SessionService,
)
from app.tools import (
    ToolCall,
    ToolDefinition,
    ToolError,
    ToolExecutor,
    ToolResult,
)


class RecordingChatService(ChatService):
    """Return queued generations while recording message histories."""

    def __init__(self, responses: list[GenerationResponse]) -> None:
        self.responses = list(responses)
        self.build_requests: list[ChatRequest] = []
        self.message_calls: list[tuple[list[Message], tuple[ToolDefinition, ...]]] = []
        self.close_count = 0

    async def build_messages(self, request: ChatRequest) -> list[Message]:
        self.build_requests.append(request)
        messages: list[Message] = []
        if request.system_prompt is not None:
            messages.append(Message(role="system", content=request.system_prompt))
        messages.append(Message(role="user", content=request.user_prompt))
        return messages

    async def chat_messages(
        self,
        messages: list[Message],
        *,
        tools: tuple[ToolDefinition, ...] = (),
    ) -> GenerationResponse:
        self.message_calls.append((list(messages), tools))
        return self.responses.pop(0)

    def close(self) -> None:
        """Record unexpected lifecycle management."""
        self.close_count += 1


class RecordingToolExecutor(ToolExecutor):
    """Return successful results while recording call order."""

    def __init__(self) -> None:
        self.calls: list[ToolCall] = []
        self.close_count = 0

    async def execute(self, call: ToolCall) -> ToolResult:
        self.calls.append(call)
        return ToolResult(content=f"result-{call.tool_name}")

    def close(self) -> None:
        """Record unexpected lifecycle management."""
        self.close_count += 1


class FailingToolExecutor(RecordingToolExecutor):
    """Raise a configured tool error."""

    def __init__(self, error: ToolError) -> None:
        super().__init__()
        self.error = error

    async def execute(self, call: ToolCall) -> ToolResult:
        self.calls.append(call)
        raise self.error


class CountingSessionStore(InMemorySessionStore):
    """Record replacement saves while retaining in-memory behavior."""

    def __init__(self) -> None:
        super().__init__()
        self.saved: list[Session] = []

    async def save(self, session: Session) -> None:
        self.saved.append(session)
        await super().save(session)


class FailingSessionService(SessionService):
    """Raise a configured session error from load or save."""

    def __init__(self, *, fail_on: str) -> None:
        super().__init__(InMemorySessionStore())
        self.fail_on = fail_on
        self.close_count = 0

    async def get_or_create(self, session_id: str) -> Session:
        if self.fail_on == "load":
            raise SessionError("load failed")
        return await super().get_or_create(session_id)

    async def save_session(self, session: Session) -> None:
        if self.fail_on == "save":
            raise SessionError("save failed")
        await super().save_session(session)

    def close(self) -> None:
        """Record unexpected lifecycle management."""
        self.close_count += 1


def definition() -> ToolDefinition:
    """Create the advertised tool definition."""
    return ToolDefinition(name="search", description="Search documents")


def request() -> ChatRequest:
    """Create an input request for loop tests."""
    return ChatRequest(user_prompt="question", system_prompt="system")


def test_loop_returns_direct_answer_without_executing_tools() -> None:
    chat_service = RecordingChatService([GenerationResponse(text="answer")])
    executor = RecordingToolExecutor()
    agent = AgentLoop(chat_service, executor, (definition(),))
    original = request()

    result = asyncio.run(agent.run(original))

    assert result == AgentResult(
        response="answer",
        messages=(
            Message(role="system", content="system"),
            Message(role="user", content="question"),
            Message(role="assistant", content="answer"),
        ),
        final_state=AgentExecutionState(
            phase=AgentPhase.FINISHED,
            messages=(
                Message(role="system", content="system"),
                Message(role="user", content="question"),
                Message(role="assistant", content="answer"),
            ),
            iteration=1,
        ),
    )
    assert chat_service.build_requests == [original]
    assert chat_service.build_requests[0] is original
    assert len(chat_service.message_calls) == 1
    assert executor.calls == []
    assert chat_service.close_count == 0
    assert executor.close_count == 0


def test_loop_returns_tool_result_to_second_chat_call() -> None:
    call = ToolCall(tool_name="search", arguments={}, call_id="call_1")
    chat_service = RecordingChatService(
        [
            GenerationResponse(text="", tool_calls=(call,)),
            GenerationResponse(text="final answer"),
        ]
    )
    executor = RecordingToolExecutor()
    tool = definition()

    result = asyncio.run(AgentLoop(chat_service, executor, (tool,)).run(request()))

    assert executor.calls == [call]
    assert len(chat_service.message_calls) == 2
    assert chat_service.message_calls[0][1] == (tool,)
    second_messages = chat_service.message_calls[1][0]
    assert second_messages[-2] == Message(
        role="assistant",
        content="",
        tool_calls=(call,),
    )
    assert second_messages[-1] == Message(
        role="tool",
        content="result-search",
        tool_call_id="call_1",
    )
    assert result.response == "final answer"
    assert result.messages[-1] == Message(
        role="assistant",
        content="final answer",
    )
    assert result.final_state.phase is AgentPhase.FINISHED
    assert result.final_state.messages == result.messages
    assert result.final_state.iteration == 2


def test_loop_executes_multiple_tools_in_provider_order() -> None:
    first = ToolCall(tool_name="first", arguments={}, call_id="call_1")
    second = ToolCall(tool_name="second", arguments={}, call_id="call_2")
    chat_service = RecordingChatService(
        [
            GenerationResponse(text="", tool_calls=(first, second)),
            GenerationResponse(text="done"),
        ]
    )
    executor = RecordingToolExecutor()

    asyncio.run(AgentLoop(chat_service, executor, ()).run(request()))

    assert executor.calls == [first, second]
    second_messages = chat_service.message_calls[1][0]
    assert [message.tool_call_id for message in second_messages[-2:]] == [
        "call_1",
        "call_2",
    ]


def test_loop_uses_explicit_tool_flow_states(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    phases: list[AgentPhase] = []

    class RecordingStateMachine(AgentStateMachine):
        """Record phase transitions while retaining state-machine behavior."""

        def transition(
            self,
            next_phase: AgentPhase,
            *,
            messages: tuple[Message, ...] | None = None,
            iteration: int | None = None,
        ) -> None:
            super().transition(
                next_phase,
                messages=messages,
                iteration=iteration,
            )
            phases.append(next_phase)

    monkeypatch.setattr(
        "app.agents.loop.AgentStateMachine",
        RecordingStateMachine,
    )
    call = ToolCall(tool_name="search", arguments={}, call_id="call_1")
    chat_service = RecordingChatService(
        [
            GenerationResponse(text="", tool_calls=(call,)),
            GenerationResponse(text="done"),
        ]
    )

    result = asyncio.run(
        AgentLoop(chat_service, RecordingToolExecutor(), ()).run(request())
    )

    assert phases == [
        AgentPhase.THINKING,
        AgentPhase.TOOL_EXECUTION,
        AgentPhase.OBSERVATION,
        AgentPhase.THINKING,
        AgentPhase.FINISHED,
    ]
    assert result.final_state.iteration == 2


def test_loop_converts_tool_error_to_tool_message_and_continues() -> None:
    call = ToolCall(tool_name="search", arguments={}, call_id="call_1")
    chat_service = RecordingChatService(
        [
            GenerationResponse(text="", tool_calls=(call,)),
            GenerationResponse(text="recovered"),
        ]
    )
    executor = FailingToolExecutor(ToolError(""))

    result = asyncio.run(AgentLoop(chat_service, executor, ()).run(request()))

    assert result.response == "recovered"
    assert chat_service.message_calls[1][0][-1] == Message(
        role="tool",
        content="Tool execution failed",
        tool_call_id="call_1",
    )


def test_loop_rejects_missing_call_id_without_execution() -> None:
    call = ToolCall(tool_name="search", arguments={})
    chat_service = RecordingChatService(
        [GenerationResponse(text="", tool_calls=(call,))]
    )
    executor = RecordingToolExecutor()

    agent = AgentLoop(chat_service, executor, ())

    with pytest.raises(AgentLoopError, match="ID"):
        asyncio.run(agent.run(request()))

    assert executor.calls == []
    assert agent._state_machine.state.phase is AgentPhase.FAILED
    assert agent._state_machine.state.iteration == 1


def test_loop_enforces_maximum_provider_calls() -> None:
    call = ToolCall(tool_name="search", arguments={}, call_id="call_1")
    chat_service = RecordingChatService(
        [GenerationResponse(text="", tool_calls=(call,))]
    )

    agent = AgentLoop(
        chat_service,
        RecordingToolExecutor(),
        (),
        max_iterations=1,
    )

    with pytest.raises(AgentLoopError, match="maximum provider calls"):
        asyncio.run(agent.run(request()))

    assert len(chat_service.message_calls) == 1
    assert agent._state_machine.state.phase is AgentPhase.FAILED
    assert agent._state_machine.state.iteration == 1


def test_loop_rejects_non_positive_max_iterations() -> None:
    with pytest.raises(AgentLoopError, match="max_iterations"):
        AgentLoop(
            RecordingChatService([]),
            RecordingToolExecutor(),
            (),
            max_iterations=0,
        )


def test_loop_preserves_positional_max_iterations_compatibility() -> None:
    agent = AgentLoop(
        RecordingChatService([]),
        RecordingToolExecutor(),
        (),
        2,
    )

    assert agent._max_iterations == 2


def test_loop_requires_session_dependencies_to_be_keyword_only() -> None:
    service = SessionService(InMemorySessionStore())

    with pytest.raises(TypeError):
        AgentLoop(
            RecordingChatService([]),
            RecordingToolExecutor(),
            (),
            5,
            service,
            "session-1",
        )


def test_loop_rejects_session_service_without_session_id() -> None:
    with pytest.raises(AgentLoopError, match="Session ID"):
        AgentLoop(
            RecordingChatService([]),
            RecordingToolExecutor(),
            (),
            session_service=SessionService(InMemorySessionStore()),
        )


def test_loop_loads_history_and_replaces_final_session_once() -> None:
    store = CountingSessionStore()
    history = Message(role="user", content="previous question")
    existing = Session(session_id="session-1", messages=(history,))
    asyncio.run(store.save(existing))
    store.saved.clear()
    service = SessionService(store)
    chat_service = RecordingChatService([GenerationResponse(text="answer")])

    result = asyncio.run(
        AgentLoop(
            chat_service,
            RecordingToolExecutor(),
            (),
            session_service=service,
            session_id="session-1",
        ).run(request())
    )

    assert chat_service.message_calls[0][0][0] is history
    assert result.messages == (
        history,
        Message(role="system", content="system"),
        Message(role="user", content="question"),
        Message(role="assistant", content="answer"),
    )
    assert store.saved == [Session(session_id="session-1", messages=result.messages)]
    assert store.saved[0].messages.count(history) == 1


@pytest.mark.parametrize(
    ("fail_on", "message"),
    [
        ("load", "loading"),
        ("save", "saving"),
    ],
)
def test_loop_converts_session_errors_and_preserves_cause(
    fail_on: str,
    message: str,
) -> None:
    service = FailingSessionService(fail_on=fail_on)
    agent = AgentLoop(
        RecordingChatService([GenerationResponse(text="answer")]),
        RecordingToolExecutor(),
        (),
        session_service=service,
        session_id="session-1",
    )

    with pytest.raises(AgentLoopError, match=message) as captured:
        asyncio.run(agent.run(request()))

    assert isinstance(captured.value.__cause__, SessionError)
    assert agent._state_machine.state.phase is AgentPhase.FAILED
    assert service.close_count == 0
