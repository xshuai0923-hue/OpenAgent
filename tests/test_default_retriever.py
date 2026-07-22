"""Tests for the default retriever implementation."""

import asyncio
from pathlib import Path

import pytest

from app.documents import Chunk
from app.embeddings import EmbeddingProvider, EmbeddingRequest, EmbeddingResponse
from app.retrievers import (
    DefaultRetriever,
    RetrievalRequest,
    RetrievalResult,
    Retriever,
    RetrieverError,
)
from app.vectorstores import SearchResult, VectorRecord, VectorStore


class RecordingEmbeddingProvider(EmbeddingProvider):
    """Return a configured response while recording requests."""

    def __init__(self, response: EmbeddingResponse) -> None:
        self.response = response
        self.requests: list[EmbeddingRequest] = []

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self.requests.append(request)
        return self.response


class FailingEmbeddingProvider(EmbeddingProvider):
    """Raise a configured exception for error-conversion tests."""

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise RuntimeError("provider failure")


class RecordingVectorStore(VectorStore):
    """Return configured results while recording searches."""

    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results
        self.searches: list[tuple[list[float], int]] = []

    async def add(self, records: list[VectorRecord]) -> None:
        return None

    async def search(
        self,
        embedding: list[float],
        *,
        top_k: int = 5,
    ) -> list[SearchResult]:
        self.searches.append((embedding, top_k))
        return self.results


class FailingVectorStore(VectorStore):
    """Raise an exception when searched."""

    async def add(self, records: list[VectorRecord]) -> None:
        return None

    async def search(
        self,
        embedding: list[float],
        *,
        top_k: int = 5,
    ) -> list[SearchResult]:
        raise RuntimeError("store failure")


def search_result() -> SearchResult:
    """Create a search result used by retriever tests."""
    return SearchResult(
        chunk=Chunk(content="content", source=Path("document.txt"), index=0),
        score=0.75,
    )


def malformed_response(embeddings: list[list[float]]) -> EmbeddingResponse:
    """Build a malformed provider response without model validation."""
    response = object.__new__(EmbeddingResponse)
    object.__setattr__(response, "embeddings", embeddings)
    return response


def test_retrieve_composes_dependencies_and_preserves_inputs() -> None:
    match = search_result()
    provider = RecordingEmbeddingProvider(EmbeddingResponse(embeddings=[[1.0, 2.0]]))
    store = RecordingVectorStore([match])
    retriever = DefaultRetriever(provider, store)
    request = RetrievalRequest(query="  original query  ", top_k=3)

    result = asyncio.run(retriever.retrieve(request))

    assert isinstance(retriever, Retriever)
    assert result == RetrievalResult(results=[match])
    assert result.results[0] is match
    assert provider.requests == [EmbeddingRequest(texts=[request.query])]
    assert store.searches == [([1.0, 2.0], request.top_k)]
    assert request == RetrievalRequest(query="  original query  ", top_k=3)


def test_retrieve_allows_empty_results() -> None:
    provider = RecordingEmbeddingProvider(EmbeddingResponse(embeddings=[[1.0]]))
    store = RecordingVectorStore([])

    result = asyncio.run(
        DefaultRetriever(provider, store).retrieve(RetrievalRequest(query="query"))
    )

    assert result.results == []
    assert len(provider.requests) == 1
    assert len(store.searches) == 1


@pytest.mark.parametrize("embeddings", [[], [[]], [[1.0], [2.0]]])
def test_retrieve_rejects_invalid_provider_embedding_count(
    embeddings: list[list[float]],
) -> None:
    provider = RecordingEmbeddingProvider(malformed_response(embeddings))
    store = RecordingVectorStore([])

    with pytest.raises(RetrieverError, match="one embedding"):
        asyncio.run(
            DefaultRetriever(provider, store).retrieve(RetrievalRequest(query="query"))
        )

    assert store.searches == []


def test_retrieve_converts_embedding_provider_exception() -> None:
    retriever = DefaultRetriever(FailingEmbeddingProvider(), RecordingVectorStore([]))

    with pytest.raises(RetrieverError, match="Embedding provider failed"):
        asyncio.run(retriever.retrieve(RetrievalRequest(query="query")))


def test_retrieve_converts_vector_store_exception() -> None:
    provider = RecordingEmbeddingProvider(EmbeddingResponse(embeddings=[[1.0]]))
    retriever = DefaultRetriever(provider, FailingVectorStore())

    with pytest.raises(RetrieverError, match="Vector store search failed"):
        asyncio.run(retriever.retrieve(RetrievalRequest(query="query")))
