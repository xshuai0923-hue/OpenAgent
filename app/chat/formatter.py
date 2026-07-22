"""Formatting of user prompts with optional retrieved context."""

from app.rag.context import RagContext


class ChatPromptFormatter:
    """Apply the public chat context template without changing its inputs."""

    @staticmethod
    def format(*, user_prompt: str, context: RagContext | None) -> str:
        """Return the original prompt or prefix it with ordered context chunks."""
        if context is None or not context.chunks:
            return user_prompt

        chunk_content = "\n\n".join(chunk.content for chunk in context.chunks)
        return f"Context:\n{chunk_content}\n\nQuestion:\n{user_prompt}"
