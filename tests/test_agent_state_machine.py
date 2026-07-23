"""Tests for explicit agent execution state transitions."""

import pytest

from app.agents import (
    AgentExecutionState,
    AgentPhase,
    AgentStateError,
    AgentStateMachine,
)
from app.providers.models import Message


def initial_state() -> AgentExecutionState:
    """Create the initial state used by state-machine tests."""
    return AgentExecutionState(
        phase=AgentPhase.INIT,
        messages=(),
        iteration=0,
    )


def test_agent_phase_members_and_values() -> None:
    assert [(phase.name, phase.value) for phase in AgentPhase] == [
        ("INIT", "init"),
        ("THINKING", "thinking"),
        ("TOOL_EXECUTION", "tool_execution"),
        ("OBSERVATION", "observation"),
        ("FINISHED", "finished"),
        ("FAILED", "failed"),
    ]


def test_state_machine_supports_successful_tool_flow() -> None:
    machine = AgentStateMachine(initial_state())
    old_state = machine.state
    messages = (Message(role="user", content="question"),)

    machine.transition(AgentPhase.THINKING, messages=messages)
    machine.transition(
        AgentPhase.TOOL_EXECUTION,
        iteration=1,
    )
    machine.transition(AgentPhase.OBSERVATION)
    machine.transition(AgentPhase.THINKING)
    machine.transition(AgentPhase.FINISHED)

    assert old_state == initial_state()
    assert machine.state == AgentExecutionState(
        phase=AgentPhase.FINISHED,
        messages=messages,
        iteration=1,
    )


@pytest.mark.parametrize(
    ("start", "next_phase"),
    [
        (AgentPhase.INIT, AgentPhase.FAILED),
        (AgentPhase.THINKING, AgentPhase.FAILED),
        (AgentPhase.TOOL_EXECUTION, AgentPhase.FAILED),
        (AgentPhase.OBSERVATION, AgentPhase.FAILED),
    ],
)
def test_non_terminal_states_can_fail(
    start: AgentPhase,
    next_phase: AgentPhase,
) -> None:
    machine = AgentStateMachine(
        AgentExecutionState(phase=start, messages=(), iteration=0)
    )

    machine.transition(next_phase)

    assert machine.state.phase is AgentPhase.FAILED


@pytest.mark.parametrize(
    ("start", "next_phase"),
    [
        (AgentPhase.INIT, AgentPhase.FINISHED),
        (AgentPhase.THINKING, AgentPhase.OBSERVATION),
        (AgentPhase.FINISHED, AgentPhase.THINKING),
        (AgentPhase.FINISHED, AgentPhase.FAILED),
        (AgentPhase.FAILED, AgentPhase.THINKING),
        (AgentPhase.FAILED, AgentPhase.TOOL_EXECUTION),
    ],
)
def test_state_machine_rejects_illegal_transitions(
    start: AgentPhase,
    next_phase: AgentPhase,
) -> None:
    machine = AgentStateMachine(
        AgentExecutionState(phase=start, messages=(), iteration=0)
    )

    with pytest.raises(AgentStateError, match="Illegal agent transition"):
        machine.transition(next_phase)

    assert machine.state.phase is start
