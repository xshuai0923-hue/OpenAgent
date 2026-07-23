"""OpenAI-compatible provider implementation."""

import json
from typing import Any

import httpx

from app.providers.base import BaseProvider
from app.providers.exceptions import ProviderError
from app.providers.models import (
    GenerationRequest,
    GenerationResponse,
    Message,
    ProviderConfig,
)
from app.tools.exceptions import ToolError
from app.tools.models import ToolCall


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
                self._message_payload(message) for message in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": definition.name,
                        "description": definition.description,
                        "parameters": {},
                    },
                }
                for definition in request.tools
            ]

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
            message = data["choices"][0]["message"]
            content = message["content"]
            raw_tool_calls = message.get("tool_calls", [])
        except (IndexError, KeyError, TypeError, ValueError) as error:
            raise ProviderError("Provider returned an invalid response") from error

        if not isinstance(raw_tool_calls, list):
            raise ProviderError("Provider returned an invalid response")
        if content is None and raw_tool_calls:
            content = ""
        if not isinstance(content, str):
            raise ProviderError("Provider returned an invalid response")

        tool_calls: list[ToolCall] = []
        for raw_tool_call in raw_tool_calls:
            try:
                function = raw_tool_call["function"]
                call_id = raw_tool_call["id"]
                name = function["name"]
                raw_arguments = function["arguments"]
            except (KeyError, TypeError) as error:
                raise ProviderError("Provider returned an invalid tool call") from error

            if not isinstance(call_id, str) or not call_id.strip():
                raise ProviderError("Provider returned an invalid tool call")
            if not isinstance(name, str) or not name.strip():
                raise ProviderError("Provider returned an invalid tool call")
            if not isinstance(raw_arguments, str):
                raise ProviderError("Provider returned invalid tool arguments")

            try:
                arguments = json.loads(raw_arguments)
            except (json.JSONDecodeError, TypeError) as error:
                raise ProviderError(
                    "Provider returned invalid tool arguments"
                ) from error

            if not isinstance(arguments, dict):
                raise ProviderError("Provider returned invalid tool arguments")

            try:
                tool_calls.append(
                    ToolCall(
                        tool_name=name,
                        arguments=arguments,
                        call_id=call_id,
                    )
                )
            except ToolError as error:
                raise ProviderError("Provider returned an invalid tool call") from error

        return GenerationResponse(text=content, tool_calls=tuple(tool_calls))

    @staticmethod
    def _message_payload(message: Message) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "role": message.role,
            "content": message.content,
        }
        if message.role == "tool":
            payload["tool_call_id"] = message.tool_call_id
        if message.tool_calls:
            payload["tool_calls"] = [
                {
                    "id": tool_call.call_id,
                    "type": "function",
                    "function": {
                        "name": tool_call.tool_name,
                        "arguments": json.dumps(
                            dict(tool_call.arguments),
                            separators=(",", ":"),
                        ),
                    },
                }
                for tool_call in message.tool_calls
            ]
        return payload

    async def close(self) -> None:
        """Close the provider HTTP client and release its resources."""
        await self._client.aclose()
