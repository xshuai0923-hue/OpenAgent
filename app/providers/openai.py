"""OpenAI-compatible provider implementation."""

from typing import Any

import httpx

from app.providers.base import BaseProvider
from app.providers.exceptions import ProviderError
from app.providers.models import GenerationRequest, GenerationResponse, ProviderConfig


class OpenAIProvider(BaseProvider):
    """Generate text through an OpenAI-compatible HTTP API."""

    def __init__(
        self,
        config: ProviderConfig,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Initialize a reusable asynchronous HTTP client."""
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=f"{config.base_url.rstrip('/')}/",
            timeout=config.timeout,
            headers={"Authorization": f"Bearer {config.api_key}"},
            transport=transport,
        )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Send a generation request and return the generated text."""
        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        try:
            response = await self._client.post("chat/completions", json=payload)
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise ProviderError("Provider request timed out") from error
        except httpx.HTTPStatusError as error:
            raise ProviderError("Provider returned an HTTP error") from error
        except httpx.RequestError as error:
            raise ProviderError("Provider connection failed") from error

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (IndexError, KeyError, TypeError, ValueError) as error:
            raise ProviderError("Provider returned an invalid response") from error

        if not isinstance(content, str):
            raise ProviderError("Provider returned an invalid response")

        return GenerationResponse(text=content)

    async def close(self) -> None:
        """Close the provider HTTP client and release its resources."""
        await self._client.aclose()
