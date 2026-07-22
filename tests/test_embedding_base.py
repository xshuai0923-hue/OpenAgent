"""Tests for the embedding provider abstract interface."""

import asyncio

import pytest

from app.embeddings import EmbeddingProvider, EmbeddingRequest, EmbeddingResponse


class DummyEmbeddingProvider(EmbeddingProvider):
    """Minimal implementation used to verify the provider interface."""

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        return EmbeddingResponse(
            embeddings=[[float(len(text))] for text in request.texts]
        )


def test_embedding_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        EmbeddingProvider()


def test_embedding_provider_can_be_implemented() -> None:
    provider = DummyEmbeddingProvider()
    request = EmbeddingRequest(texts=["one", "three"])

    response = asyncio.run(provider.embed(request))

    assert isinstance(response, EmbeddingResponse)
    assert response.embeddings == [[3.0], [5.0]]
