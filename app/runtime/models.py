"""Implementation-independent runtime data models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeRequest:
    """Describe one runtime request and its enabled capabilities."""

    user_prompt: str
    system_prompt: str | None
    enable_rag: bool
    enable_tools: bool


@dataclass(frozen=True)
class RuntimeResponse:
    """Contain the final text produced by a runtime."""

    response: str
