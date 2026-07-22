"""Tests for the OpenAI-compatible embedding provider."""

from collections.abc import Callable

import httpx
import pytest

from app.embeddings import (
    EmbeddingError,
    EmbeddingProvider,
    EmbeddingProviderConfig,
    EmbeddingRequest,
    OpenAIEmbeddingProvider,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def provider_config() -> EmbeddingProviderConfig:
    return EmbeddingProviderConfig(
        api_key="test-key",
        base_url="https://example.com/v1",
        model="embedding-model",
        timeout=10,
    )


def test_embedding_provider_config_validates_required_values() -> None:
    with pytest.raises(EmbeddingError, match="API key"):
        EmbeddingProviderConfig(
            api_key=" ", base_url="https://example.com", model="model", timeout=1
        )
    with pytest.raises(EmbeddingError, match="valid HTTP URL"):
        EmbeddingProviderConfig(
            api_key="key", base_url="not-a-url", model="model", timeout=1
        )
    with pytest.raises(EmbeddingError, match="model"):
        EmbeddingProviderConfig(
            api_key="key", base_url="https://example.com", model=" ", timeout=1
        )
    with pytest.raises(EmbeddingError, match="timeout"):
        EmbeddingProviderConfig(
            api_key="key", base_url="https://example.com", model="model", timeout=0
        )


def test_embedding_provider_config_hides_api_key() -> None:
    config = EmbeddingProviderConfig(
        api_key="secret",
        base_url="https://example.com",
        model="model",
        timeout=1,
    )

    assert "secret" not in repr(config)


def create_provider(
    config: EmbeddingProviderConfig,
    handler: Callable[[httpx.Request], httpx.Response],
) -> OpenAIEmbeddingProvider:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OpenAIEmbeddingProvider(config, client=client)


@pytest.mark.anyio
async def test_embed_constructs_request_and_preserves_order(
    provider_config: EmbeddingProviderConfig,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == "https://example.com/v1/embeddings"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.read() == (
            b'{"model":"embedding-model","input":["first","second"]}'
        )
        return httpx.Response(
            200,
            json={
                "data": [
                    {"embedding": [0.1, 0.2]},
                    {"embedding": [0.3, 0.4]},
                ]
            },
        )

    provider = create_provider(provider_config, handler)
    try:
        response = await provider.embed(EmbeddingRequest(texts=["first", "second"]))
    finally:
        await provider.close()

    assert response.embeddings == [[0.1, 0.2], [0.3, 0.4]]
    assert isinstance(provider, EmbeddingProvider)


@pytest.mark.anyio
async def test_embed_converts_http_error(
    provider_config: EmbeddingProviderConfig,
) -> None:
    provider = create_provider(
        provider_config,
        lambda request: httpx.Response(500, request=request),
    )
    try:
        with pytest.raises(EmbeddingError, match="HTTP error"):
            await provider.embed(EmbeddingRequest(texts=["text"]))
    finally:
        await provider.close()


@pytest.mark.anyio
async def test_embed_converts_network_error(
    provider_config: EmbeddingProviderConfig,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    provider = create_provider(provider_config, handler)
    try:
        with pytest.raises(EmbeddingError, match="connection failed"):
            await provider.embed(EmbeddingRequest(texts=["text"]))
    finally:
        await provider.close()


@pytest.mark.anyio
async def test_embed_converts_timeout(
    provider_config: EmbeddingProviderConfig,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    provider = create_provider(provider_config, handler)
    try:
        with pytest.raises(EmbeddingError, match="timed out"):
            await provider.embed(EmbeddingRequest(texts=["text"]))
    finally:
        await provider.close()


@pytest.mark.anyio
async def test_embed_converts_invalid_json(
    provider_config: EmbeddingProviderConfig,
) -> None:
    provider = create_provider(
        provider_config,
        lambda request: httpx.Response(200, content=b"not-json", request=request),
    )
    try:
        with pytest.raises(EmbeddingError, match="invalid response"):
            await provider.embed(EmbeddingRequest(texts=["text"]))
    finally:
        await provider.close()


@pytest.mark.anyio
async def test_embed_rejects_response_count_mismatch(
    provider_config: EmbeddingProviderConfig,
) -> None:
    provider = create_provider(
        provider_config,
        lambda request: httpx.Response(
            200,
            json={"data": [{"embedding": [0.1]}]},
            request=request,
        ),
    )
    try:
        with pytest.raises(EmbeddingError, match="count"):
            await provider.embed(EmbeddingRequest(texts=["first", "second"]))
    finally:
        await provider.close()


@pytest.mark.anyio
async def test_embed_rejects_empty_embedding(
    provider_config: EmbeddingProviderConfig,
) -> None:
    provider = create_provider(
        provider_config,
        lambda request: httpx.Response(
            200,
            json={"data": [{"embedding": []}]},
            request=request,
        ),
    )
    try:
        with pytest.raises(EmbeddingError, match="invalid response"):
            await provider.embed(EmbeddingRequest(texts=["text"]))
    finally:
        await provider.close()


@pytest.mark.anyio
async def test_embed_rejects_non_numeric_embedding(
    provider_config: EmbeddingProviderConfig,
) -> None:
    provider = create_provider(
        provider_config,
        lambda request: httpx.Response(
            200,
            json={"data": [{"embedding": [True]}]},
            request=request,
        ),
    )
    try:
        with pytest.raises(EmbeddingError, match="invalid response"):
            await provider.embed(EmbeddingRequest(texts=["text"]))
    finally:
        await provider.close()


@pytest.mark.anyio
async def test_close_releases_injected_client(
    provider_config: EmbeddingProviderConfig,
) -> None:
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: None))
    provider = OpenAIEmbeddingProvider(provider_config, client=client)

    await provider.close()

    assert client.is_closed
