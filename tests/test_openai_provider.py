"""Tests for the OpenAI-compatible provider."""

from collections.abc import Callable

import httpx
import pytest

from app.providers import (
    BaseProvider,
    GenerationRequest,
    GenerationResponse,
    OpenAIProvider,
    ProviderConfig,
    ProviderError,
)
from app.providers.models import Message
from app.tools import ToolCall, ToolDefinition


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
    assert response.tool_calls == ()
    assert isinstance(provider, BaseProvider)


@pytest.mark.anyio
async def test_generate_maps_tools_and_parses_tool_calls(
    provider_config: ProviderConfig,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.read() == (
            b'{"model":"test-model","messages":[{"role":"user",'
            b'"content":"hello"}],"temperature":0.7,"max_tokens":1024,'
            b'"tools":[{"type":"function","function":{"name":"search",'
            b'"description":"Search documents","parameters":{}}}]}'
        )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "I will search",
                            "tool_calls": [
                                {
                                    "id": "call_123",
                                    "type": "function",
                                    "function": {
                                        "name": "search",
                                        "arguments": '{"query":"hello"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
        )

    provider = create_provider(provider_config, handler)
    try:
        response = await provider.generate(
            GenerationRequest(
                messages=[Message(role="user", content="hello")],
                tools=(ToolDefinition(name="search", description="Search documents"),),
            )
        )
    finally:
        await provider.close()

    assert response == GenerationResponse(
        text="I will search",
        tool_calls=(
            ToolCall(
                tool_name="search",
                arguments={"query": "hello"},
                call_id="call_123",
            ),
        ),
    )


@pytest.mark.anyio
async def test_generate_maps_tool_result_message(
    provider_config: ProviderConfig,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.read() == (
            b'{"model":"test-model","messages":[{"role":"tool",'
            b'"content":"result","tool_call_id":"call_123"}],'
            b'"temperature":0.7,"max_tokens":1024}'
        )
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "done"}}]},
        )

    provider = create_provider(provider_config, handler)
    try:
        response = await provider.generate(
            GenerationRequest(
                messages=[
                    Message(
                        role="tool",
                        content="result",
                        tool_call_id="call_123",
                    )
                ]
            )
        )
    finally:
        await provider.close()

    assert response == GenerationResponse(text="done")


@pytest.mark.anyio
async def test_generate_maps_assistant_tool_calls_and_tool_message(
    provider_config: ProviderConfig,
) -> None:
    call = ToolCall(
        tool_name="search",
        arguments={"query": "hello"},
        call_id="call_123",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.read() == (
            b'{"model":"test-model","messages":[{"role":"assistant",'
            b'"content":"","tool_calls":[{"id":"call_123","type":"function",'
            b'"function":{"name":"search","arguments":"{\\"query\\":\\"hello\\"}"}}]},'
            b'{"role":"tool","content":"result","tool_call_id":"call_123"}],'
            b'"temperature":0.7,"max_tokens":1024}'
        )
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "done"}}]},
        )

    provider = create_provider(provider_config, handler)
    try:
        response = await provider.generate(
            GenerationRequest(
                messages=[
                    Message(role="assistant", content="", tool_calls=(call,)),
                    Message(
                        role="tool",
                        content="result",
                        tool_call_id="call_123",
                    ),
                ]
            )
        )
    finally:
        await provider.close()

    assert response == GenerationResponse(text="done")


@pytest.mark.anyio
@pytest.mark.parametrize(
    "function",
    [
        {"name": "search", "arguments": "not-json"},
        {"name": "search", "arguments": "[]"},
        {"arguments": "{}"},
    ],
)
async def test_generate_rejects_invalid_tool_calls(
    provider_config: ProviderConfig,
    function: dict[str, object],
) -> None:
    provider = create_provider(
        provider_config,
        lambda request: httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "tool call",
                            "tool_calls": [{"id": "call_123", "function": function}],
                        }
                    }
                ]
            },
            request=request,
        ),
    )
    try:
        with pytest.raises(ProviderError, match="invalid"):
            await provider.generate(generation_request())
    finally:
        await provider.close()


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
