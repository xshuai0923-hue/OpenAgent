"""Abstract interface for language model providers."""

from abc import ABC, abstractmethod

from app.providers.models import GenerationRequest, GenerationResponse


class BaseProvider(ABC):
    """Define the common interface implemented by every LLM provider."""

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a response for the supplied request."""
        raise NotImplementedError
