"""Tests for the retrieval-augmented context service."""

import asyncio
from pathlib import Path

import pytest

from app.documents import Chunk
from app.rag import RagService, RagServiceError
from app.retrievers import RetrievalRequest, RetrievalResult, Retriever, RetrieverError
from app.vectorstores import SearchResult


class RecordingRetriever(Retriever):
    """Return configured retrieval results while recording requests."""

    def __init__(self, result: RetrievalResult) -> None:
        self.result = result
        self.requests: list[RetrievalRequest] = []

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        self.requests.append(request)
        return self.result


class FailingRetriever(Retriever):
    """Raise a retriever error for conversion tests."""

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        raise RetrieverError("retrieval failed")


def test_retrieve_context_extracts_original_chunks() -> None:
    first = Chunk(content="first", source=Path("document.txt"), index=0)
    second = Chunk(content="second", source=Path("document.txt"), index=1)
    retriever = RecordingRetriever(
        RetrievalResult(
            results=[
                SearchResult(chunk=first, score=0.9),
                SearchResult(chunk=second, score=0.8),
            ]
        )
    )
    service = RagService(retriever)
    request = RetrievalRequest(query="  original query  ", top_k=2)

    context = asyncio.run(service.retrieve_context(request))

    assert context.chunks == [first, second]
    assert context.chunks[0] is first
    assert context.chunks[1] is second
    assert retriever.requests == [request]
    assert retriever.requests[0] is request
    assert request == RetrievalRequest(query="  original query  ", top_k=2)


def test_retrieve_context_allows_empty_results() -> None:
    retriever = RecordingRetriever(RetrievalResult(results=[]))

    context = asyncio.run(
        RagService(retriever).retrieve_context(RetrievalRequest(query="query"))
    )

    assert context.chunks == []
    assert len(retriever.requests) == 1


def test_retrieve_context_converts_retriever_error() -> None:
    service = RagService(FailingRetriever())

    with pytest.raises(RagServiceError, match="Context retrieval failed"):
        asyncio.run(service.retrieve_context(RetrievalRequest(query="query")))
