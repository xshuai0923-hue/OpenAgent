"""State data model for agent runtime execution."""

from dataclasses import dataclass

from app.runtime.models import RuntimeRequest, RuntimeResponse


@dataclass(frozen=True)
class AgentState:
    """Contain the original runtime input and its optional output."""

    request: RuntimeRequest
    response: RuntimeResponse | None
