"""OpenAI-compatible embedding provider implementation."""

from typing import Any

import httpx

from app.embeddings.base import EmbeddingProvider
from app.embeddings.config import EmbeddingProviderConfig
from app.embeddings.exceptions import EmbeddingError
from app.embeddings.models import EmbeddingRequest, EmbeddingResponse


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Create embeddings through an OpenAI-compatible HTTP API."""

    def __init__(
        self,
        config: EmbeddingProviderConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the provider and take ownership of its HTTP client."""
        self._config = config
        self._client = client if client is not None else httpx.AsyncClient()

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Request embeddings and return vectors in response order."""
        url = f"{self._config.base_url.rstrip('/')}/embeddings"
        payload = {"model": self._config.model, "input": request.texts}

        try:
            response = await self._client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {self._config.api_key}"},
                timeout=self._config.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise EmbeddingError("Embedding request timed out") from error
        except httpx.HTTPStatusError as error:
            raise EmbeddingError("Embedding provider returned an HTTP error") from error
        except httpx.RequestError as error:
            raise EmbeddingError("Embedding provider connection failed") from error

        try:
            data: Any = response.json()
            raw_embeddings = data["data"]
        except (KeyError, TypeError, ValueError) as error:
            raise EmbeddingError(
                "Embedding provider returned an invalid response"
            ) from error

        if not isinstance(raw_embeddings, list):
            raise EmbeddingError("Embedding provider returned an invalid response")
        if len(raw_embeddings) != len(request.texts):
            raise EmbeddingError("Embedding response count does not match request")

        embeddings: list[list[float]] = []
        for item in raw_embeddings:
            if not isinstance(item, dict):
                raise EmbeddingError("Embedding provider returned an invalid response")
            embedding = item.get("embedding")
            if not isinstance(embedding, list) or not embedding:
                raise EmbeddingError("Embedding provider returned an invalid response")
            if any(
                isinstance(value, bool) or not isinstance(value, (int, float))
                for value in embedding
            ):
                raise EmbeddingError("Embedding provider returned an invalid response")
            embeddings.append([float(value) for value in embedding])

        return EmbeddingResponse(embeddings=embeddings)

    async def close(self) -> None:
        """Close the owned HTTP client and release its resources."""
        await self._client.aclose()
