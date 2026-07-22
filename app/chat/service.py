"""Application service for orchestrating one chat turn."""

from app.chat.exceptions import ChatServiceError
from app.chat.formatter import ChatPromptFormatter
from app.chat.models import ChatRequest
from app.prompts.builder import PromptBuilder, PromptBuilderError
from app.providers.base import BaseProvider
from app.providers.exceptions import ProviderError
from app.providers.models import GenerationRequest, GenerationResponse
from app.rag.context import RagContext
from app.rag.exceptions import RagServiceError
from app.rag.service import RagService


class ChatService:
    """Coordinate optional retrieval, prompt construction, and generation."""

    def __init__(
        self,
        provider: BaseProvider,
        prompt_builder: PromptBuilder,
        rag_service: RagService | None = None,
    ) -> None:
        """Store externally managed chat dependencies."""
        self._provider = provider
        self._prompt_builder = prompt_builder
        self._rag_service = rag_service

    async def chat(self, request: ChatRequest) -> GenerationResponse:
        """Complete one chat turn and return the provider response unchanged."""
        context: RagContext | None = None
        if request.retrieval_request is not None and self._rag_service is not None:
            try:
                context = await self._rag_service.retrieve_context(
                    request.retrieval_request
                )
            except RagServiceError as error:
                raise ChatServiceError("RAG context retrieval failed") from error

        user_prompt = ChatPromptFormatter.format(
            user_prompt=request.user_prompt,
            context=context,
        )

        try:
            messages = self._prompt_builder.build(
                user_prompt=user_prompt,
                system_prompt=request.system_prompt,
            )
        except PromptBuilderError as error:
            raise ChatServiceError("Prompt construction failed") from error

        try:
            return await self._provider.generate(GenerationRequest(messages=messages))
        except ProviderError as error:
            raise ChatServiceError("Chat provider failed") from error
