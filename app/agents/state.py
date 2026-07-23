"""Execution phases for the agent state machine."""

from enum import Enum


class AgentPhase(str, Enum):
    """Identify one explicit phase of agent execution."""

    INIT = "init"
    THINKING = "thinking"
    TOOL_EXECUTION = "tool_execution"
    OBSERVATION = "observation"
    FINISHED = "finished"
    FAILED = "failed"
