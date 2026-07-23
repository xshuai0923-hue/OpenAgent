"""Tests for the agent state contract."""

from dataclasses import FrozenInstanceError

import pytest

from app.agents import AgentExecutionState, AgentPhase
from app.providers.models import Message
from app.runtime import AgentState, RuntimeRequest, RuntimeResponse


def runtime_request() -> RuntimeRequest:
    """Create a runtime request for state tests."""
    return RuntimeRequest(
        user_prompt="prompt",
        system_prompt=None,
        enable_rag=False,
        enable_tools=False,
    )


def test_agent_state_preserves_request_and_response_objects() -> None:
    request = runtime_request()
    response = RuntimeResponse(response="answer")

    state = AgentState(request=request, response=response)

    assert state.request is request
    assert state.response is response
    assert isinstance(state.request, RuntimeRequest)
    assert isinstance(state.response, RuntimeResponse)


def test_agent_state_allows_absent_response() -> None:
    request = runtime_request()

    state = AgentState(request=request, response=None)

    assert state.request is request
    assert state.response is None


def test_agent_state_is_frozen() -> None:
    state = AgentState(request=runtime_request(), response=None)

    with pytest.raises(FrozenInstanceError):
        state.response = RuntimeResponse(response="answer")


def test_agent_execution_state_preserves_fields() -> None:
    messages = (Message(role="user", content="prompt"),)

    state = AgentExecutionState(
        phase=AgentPhase.THINKING,
        messages=messages,
        iteration=1,
    )

    assert state.phase is AgentPhase.THINKING
    assert state.messages is messages
    assert state.iteration == 1


def test_agent_execution_state_is_frozen() -> None:
    state = AgentExecutionState(
        phase=AgentPhase.INIT,
        messages=(),
        iteration=0,
    )

    with pytest.raises(FrozenInstanceError):
        state.iteration = 1
