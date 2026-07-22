"""Default retriever implementation."""

from app.embeddings.base import EmbeddingProvider
from app.embeddings.models import EmbeddingRequest
from app.retrievers.base import Retriever
from app.retrievers.exceptions import RetrieverError
from app.retrievers.models import RetrievalRequest, RetrievalResult
from app.vectorstores.base import VectorStore


class DefaultRetriever(Retriever):
    """Retrieve vector-store matches using an embedding provider."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        """Store externally managed retrieval dependencies."""
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """Embed the query and return matching vector-store results."""
        try:
            response = await self._embedding_provider.embed(
                EmbeddingRequest(texts=[request.query])
            )
        except Exception as error:
            raise RetrieverError("Embedding provider failed") from error

        if len(response.embeddings) != 1 or not response.embeddings[0]:
            raise RetrieverError("Embedding provider must return one embedding")

        try:
            results = await self._vector_store.search(
                response.embeddings[0],
                top_k=request.top_k,
            )
        except Exception as error:
            raise RetrieverError("Vector store search failed") from error

        return RetrievalResult(results=results)
