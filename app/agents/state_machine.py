"""Explicit state transitions for agent execution."""

from app.agents.exceptions import AgentStateError
from app.agents.models import AgentExecutionState
from app.agents.state import AgentPhase
from app.providers.models import Message

_ALLOWED_TRANSITIONS: dict[AgentPhase, frozenset[AgentPhase]] = {
    AgentPhase.INIT: frozenset({AgentPhase.THINKING, AgentPhase.FAILED}),
    AgentPhase.THINKING: frozenset(
        {
            AgentPhase.TOOL_EXECUTION,
            AgentPhase.FINISHED,
            AgentPhase.FAILED,
        }
    ),
    AgentPhase.TOOL_EXECUTION: frozenset({AgentPhase.OBSERVATION, AgentPhase.FAILED}),
    AgentPhase.OBSERVATION: frozenset({AgentPhase.THINKING, AgentPhase.FAILED}),
    AgentPhase.FINISHED: frozenset(),
    AgentPhase.FAILED: frozenset(),
}


class AgentStateMachine:
    """Manage immutable agent execution state transitions."""

    def __init__(self, initial_state: AgentExecutionState) -> None:
        """Initialize the machine with the supplied state snapshot."""
        self._state = initial_state

    @property
    def state(self) -> AgentExecutionState:
        """Return the current immutable execution state."""
        return self._state

    def transition(
        self,
        next_phase: AgentPhase,
        *,
        messages: tuple[Message, ...] | None = None,
        iteration: int | None = None,
    ) -> None:
        """Replace the current state when the phase transition is allowed."""
        if next_phase not in _ALLOWED_TRANSITIONS[self._state.phase]:
            raise AgentStateError(
                f"Illegal agent transition: {self._state.phase.value} "
                f"-> {next_phase.value}"
            )
        self._state = AgentExecutionState(
            phase=next_phase,
            messages=self._state.messages if messages is None else messages,
            iteration=self._state.iteration if iteration is None else iteration,
        )
