"""Tests for implementation-independent retrieval models."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.documents import Chunk
from app.retrievers import RetrievalRequest, RetrievalResult, RetrieverError
from app.vectorstores import SearchResult


def test_retrieval_request_can_be_created() -> None:
    request = RetrievalRequest(query="  question  ")

    assert request.query == "  question  "
    assert request.top_k == 5


@pytest.mark.parametrize("query", ["", "   "])
def test_retrieval_request_rejects_empty_query(query: str) -> None:
    with pytest.raises(RetrieverError, match="query"):
        RetrievalRequest(query=query)


@pytest.mark.parametrize("top_k", [0, -1])
def test_retrieval_request_rejects_non_positive_top_k(top_k: int) -> None:
    with pytest.raises(RetrieverError, match="top_k"):
        RetrievalRequest(query="question", top_k=top_k)


def test_retrieval_request_is_frozen() -> None:
    request = RetrievalRequest(query="question")

    with pytest.raises(FrozenInstanceError):
        request.query = "changed"


def test_retrieval_result_preserves_search_results() -> None:
    search_result = SearchResult(
        chunk=Chunk(content="content", source=Path("document.txt"), index=0),
        score=0.9,
    )

    result = RetrievalResult(results=[search_result])

    assert result.results == [search_result]
    assert result.results[0] is search_result


def test_retrieval_result_allows_empty_results() -> None:
    assert RetrievalResult(results=[]).results == []


def test_retrieval_result_is_frozen() -> None:
    result = RetrievalResult(results=[])

    with pytest.raises(FrozenInstanceError):
        result.results = []
