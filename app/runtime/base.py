"""Abstract interface for agent runtimes."""

from abc import ABC, abstractmethod

from app.runtime.models import RuntimeRequest, RuntimeResponse


class BaseRuntime(ABC):
    """Define the implementation-independent runtime protocol."""

    @abstractmethod
    async def run(self, request: RuntimeRequest) -> RuntimeResponse:
        """Execute one runtime request and return its final response."""
        raise NotImplementedError
