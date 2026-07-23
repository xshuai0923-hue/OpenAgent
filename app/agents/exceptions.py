"""Framework-independent agent exceptions."""

from app.core.exceptions import ApplicationError


class AgentLoopError(ApplicationError):
    """Raised when an agent loop cannot produce a final response."""


class AgentStateError(AgentLoopError):
    """Raised when an agent state transition is not allowed."""
