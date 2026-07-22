"""Tests for provider-independent embedding models."""

from dataclasses import FrozenInstanceError

import pytest

from app.embeddings import EmbeddingError, EmbeddingRequest, EmbeddingResponse


def test_embedding_request_can_be_created() -> None:
    request = EmbeddingRequest(texts=["first", "second"])

    assert request.texts == ["first", "second"]


def test_embedding_request_rejects_empty_list() -> None:
    with pytest.raises(EmbeddingError, match="at least one text"):
        EmbeddingRequest(texts=[])


@pytest.mark.parametrize("text", ["", "   "])
def test_embedding_request_rejects_empty_text(text: str) -> None:
    with pytest.raises(EmbeddingError, match="must not be empty"):
        EmbeddingRequest(texts=["valid", text])


def test_embedding_request_is_frozen() -> None:
    request = EmbeddingRequest(texts=["text"])

    with pytest.raises(FrozenInstanceError):
        request.texts = []


def test_embedding_response_can_be_created() -> None:
    response = EmbeddingResponse(embeddings=[[0.1, 0.2], [0.3, 0.4]])

    assert response.embeddings == [[0.1, 0.2], [0.3, 0.4]]


def test_embedding_response_rejects_empty_list() -> None:
    with pytest.raises(EmbeddingError, match="at least one embedding"):
        EmbeddingResponse(embeddings=[])


def test_embedding_response_rejects_empty_embedding() -> None:
    with pytest.raises(EmbeddingError, match="must not be empty"):
        EmbeddingResponse(embeddings=[[0.1], []])


def test_embedding_response_is_frozen() -> None:
    response = EmbeddingResponse(embeddings=[[0.1]])

    with pytest.raises(FrozenInstanceError):
        response.embeddings = []
