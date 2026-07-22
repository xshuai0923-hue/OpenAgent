"""Tests for the retriever abstract interface."""

import asyncio

import pytest

from app.retrievers import RetrievalRequest, RetrievalResult, Retriever


class DummyRetriever(Retriever):
    """Minimal implementation used to verify the retriever interface."""

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        return RetrievalResult(results=[])


def test_retriever_is_abstract() -> None:
    with pytest.raises(TypeError):
        Retriever()


def test_retriever_can_be_implemented() -> None:
    retriever = DummyRetriever()

    result = asyncio.run(retriever.retrieve(RetrievalRequest(query="question")))

    assert isinstance(result, RetrievalResult)
    assert result.results == []
