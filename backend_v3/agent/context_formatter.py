"""Context formatting for agent consumption."""

from typing import List, Dict


class ContextFormatter:
    """Formats retrieved chunks for agent consumption."""

    @staticmethod
    def format_chunks(chunks: List[Dict]) -> str:
        """
        Format retrieved chunks as agent context.

        Args:
            chunks: Retrieved chunks with metadata

        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant content found in the book."

        formatted_parts = []

        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get("metadata", {})
            chapter = metadata.get("chapter", "Unknown")
            section = metadata.get("section", "Unknown")
            text = chunk.get("text", "")
            score = chunk.get("score", 0.0)

            formatted_parts.append(
                f"[{i}] Chapter: {chapter}, Section: {section} (Relevance: {score:.2f})\n{text}\n"
            )

        return "\n".join(formatted_parts)

    @staticmethod
    def format_selected_text_context(
        selected_text: str,
        chunks: List[Dict]
    ) -> str:
        """
        Format context for selected-text mode.

        Args:
            selected_text: User-selected text
            chunks: Retrieved chunks (constrained to selection)

        Returns:
            Formatted context with selection emphasis
        """
        if not chunks:
            return f"""SELECTED TEXT: "{selected_text}"

No relevant content found related to this selection."""

        formatted_chunks = ContextFormatter.format_chunks(chunks)

        return f"""SELECTED TEXT: "{selected_text}"

You must answer focusing on this selected text. Use ONLY the following context:

{formatted_chunks}"""

    @staticmethod
    def get_context_token_count(context: str) -> int:
        """
        Estimate token count for context.

        Args:
            context: Formatted context string

        Returns:
            Approximate token count (rough estimate: 1 token ≈ 4 characters)
        """
        return len(context) // 4

    @staticmethod
    def truncate_if_needed(
        context: str,
        max_tokens: int = 4000
    ) -> str:
        """
        Truncate context if exceeds token limit.

        Args:
            context: Formatted context
            max_tokens: Maximum allowed tokens

        Returns:
            Truncated context if needed
        """
        estimated_tokens = ContextFormatter.get_context_token_count(context)

        if estimated_tokens <= max_tokens:
            return context

        # Truncate to fit (rough approximation)
        max_chars = max_tokens * 4
        truncated = context[:max_chars]

        return truncated + "\n\n[Context truncated due to length]"
