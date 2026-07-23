"""Data models returned by agent orchestration."""

from dataclasses import dataclass

from app.agents.exceptions import AgentLoopError
from app.agents.state import AgentPhase
from app.providers.models import Message


@dataclass(frozen=True)
class AgentExecutionState:
    """Contain one immutable snapshot of agent execution."""

    phase: AgentPhase
    messages: tuple[Message, ...]
    iteration: int


@dataclass(frozen=True)
class AgentResult:
    """Contain a final response and its complete provider message history."""

    response: str
    messages: tuple[Message, ...]
    final_state: AgentExecutionState

    def __post_init__(self) -> None:
        """Reject empty responses and isolate the message tuple."""
        if not self.response.strip():
            raise AgentLoopError("Agent response must not be empty")
        object.__setattr__(self, "messages", tuple(self.messages))
