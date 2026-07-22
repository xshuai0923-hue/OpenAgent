"""Tests for the OpenAI-compatible provider."""

from collections.abc import Callable

import httpx
import pytest

from app.providers import (
    BaseProvider,
    GenerationRequest,
    OpenAIProvider,
    ProviderConfig,
    ProviderError,
)
from app.providers.models import Message


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def provider_config() -> ProviderConfig:
    return ProviderConfig(
        api_key="test-key",
        base_url="https://example.com/v1",
        model="test-model",
        timeout=10,
    )


def create_provider(
    config: ProviderConfig,
    handler: Callable[[httpx.Request], httpx.Response],
) -> OpenAIProvider:
    return OpenAIProvider(config, transport=httpx.MockTransport(handler))


def generation_request() -> GenerationRequest:
    return GenerationRequest(messages=[Message(role="user", content="hello")])


@pytest.mark.anyio
async def test_generate_constructs_request_and_parses_response(
    provider_config: ProviderConfig,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == "https://example.com/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.read() == (
            b'{"model":"test-model","messages":[{"role":"system",'
            b'"content":"Be concise"},{"role":"user","content":"hello"},'
            b'{"role":"assistant","content":"previous"}],'
            b'"temperature":0.2,"max_tokens":64}'
        )
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "world"}}]},
        )

    provider = create_provider(provider_config, handler)
    try:
        response = await provider.generate(
            GenerationRequest(
                messages=[
                    Message(role="system", content="Be concise"),
                    Message(role="user", content="hello"),
                    Message(role="assistant", content="previous"),
                ],
                temperature=0.2,
                max_tokens=64,
            )
        )
    finally:
        await provider.close()

    assert response.text == "world"
    assert isinstance(provider, BaseProvider)


@pytest.mark.anyio
async def test_generate_converts_timeout(provider_config: ProviderConfig) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    provider = create_provider(provider_config, handler)
    try:
        with pytest.raises(ProviderError, match="timed out"):
            await provider.generate(generation_request())
    finally:
        await provider.close()


@pytest.mark.anyio
async def test_generate_converts_connection_error(
    provider_config: ProviderConfig,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    provider = create_provider(provider_config, handler)
    try:
        with pytest.raises(ProviderError, match="connection failed"):
            await provider.generate(generation_request())
    finally:
        await provider.close()


@pytest.mark.anyio
async def test_generate_converts_http_error(provider_config: ProviderConfig) -> None:
    provider = create_provider(
        provider_config,
        lambda request: httpx.Response(500, request=request),
    )
    try:
        with pytest.raises(ProviderError, match="HTTP error"):
            await provider.generate(generation_request())
    finally:
        await provider.close()


@pytest.mark.anyio
async def test_generate_converts_json_error(provider_config: ProviderConfig) -> None:
    provider = create_provider(
        provider_config,
        lambda request: httpx.Response(200, content=b"not-json", request=request),
    )
    try:
        with pytest.raises(ProviderError, match="invalid response"):
            await provider.generate(generation_request())
    finally:
        await provider.close()


@pytest.mark.anyio
async def test_close_releases_client(provider_config: ProviderConfig) -> None:
    provider = create_provider(
        provider_config,
        lambda request: httpx.Response(200, request=request),
    )

    await provider.close()

    assert provider._client.is_closed
