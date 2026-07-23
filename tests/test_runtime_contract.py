"""Tests for the agent runtime contract."""

import asyncio
from dataclasses import FrozenInstanceError

import pytest

from app.core.exceptions import ApplicationError
from app.runtime import BaseRuntime, RuntimeError, RuntimeRequest, RuntimeResponse


class DummyRuntime(BaseRuntime):
    """Minimal implementation used to verify the runtime protocol."""

    async def run(self, request: RuntimeRequest) -> RuntimeResponse:
        return RuntimeResponse(response=request.user_prompt)


def test_runtime_request_preserves_fields_and_is_frozen() -> None:
    request = RuntimeRequest(
        user_prompt="prompt",
        system_prompt="system",
        enable_rag=True,
        enable_tools=False,
    )

    assert request.user_prompt == "prompt"
    assert request.system_prompt == "system"
    assert request.enable_rag is True
    assert request.enable_tools is False
    with pytest.raises(FrozenInstanceError):
        request.user_prompt = "changed"


def test_runtime_request_accepts_absent_system_prompt() -> None:
    request = RuntimeRequest(
        user_prompt="prompt",
        system_prompt=None,
        enable_rag=False,
        enable_tools=False,
    )

    assert request.system_prompt is None


def test_runtime_response_preserves_text_and_is_frozen() -> None:
    response = RuntimeResponse(response="answer")

    assert response.response == "answer"
    with pytest.raises(FrozenInstanceError):
        response.response = "changed"


def test_base_runtime_and_run_are_abstract() -> None:
    with pytest.raises(TypeError):
        BaseRuntime()

    assert BaseRuntime.__abstractmethods__ == frozenset({"run"})


def test_base_runtime_can_be_implemented() -> None:
    request = RuntimeRequest(
        user_prompt="answer",
        system_prompt=None,
        enable_rag=False,
        enable_tools=False,
    )

    response = asyncio.run(DummyRuntime().run(request))

    assert response == RuntimeResponse(response="answer")


def test_runtime_error_inherits_application_error() -> None:
    error = RuntimeError("runtime failure")

    assert isinstance(error, ApplicationError)
