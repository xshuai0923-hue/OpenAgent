"""Tests for the provider abstract interface."""

import asyncio

import pytest

from app.providers.base import BaseProvider
from app.providers.models import GenerationRequest, GenerationResponse, Message


class ConcreteProvider(BaseProvider):
    """Minimal provider implementation used to verify the interface."""

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        return GenerationResponse(text=request.messages[0].content)


def test_base_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseProvider()


def test_base_provider_can_be_implemented() -> None:
    provider = ConcreteProvider()
    request = GenerationRequest(messages=[Message(role="user", content="hello")])

    response = asyncio.run(provider.generate(request))

    assert response == GenerationResponse(text="hello")
