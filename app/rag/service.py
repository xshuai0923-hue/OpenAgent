"""Service for constructing retrieval-augmented context."""

from app.rag.context import RagContext
from app.rag.exceptions import RagServiceError
from app.retrievers.base import Retriever
from app.retrievers.exceptions import RetrieverError
from app.retrievers.models import RetrievalRequest


class RagService:
    """Construct context from results supplied by a retriever."""

    def __init__(self, retriever: Retriever) -> None:
        """Store the externally managed retriever dependency."""
        self._retriever = retriever

    async def retrieve_context(self, request: RetrievalRequest) -> RagContext:
        """Retrieve matches and expose their original chunks as context."""
        try:
            retrieval = await self._retriever.retrieve(request)
        except RetrieverError as error:
            raise RagServiceError("Context retrieval failed") from error

        return RagContext(chunks=[result.chunk for result in retrieval.results])
