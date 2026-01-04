"""Selected-text mode handling logic."""

from typing import Optional, List, Dict
from backend_v3.agent.context_formatter import ContextFormatter


class SelectedTextHandler:
    """Handles selected-text question mode."""

    @staticmethod
    def validate_selected_text(
        selected_text: Optional[str],
        retrieval_mode: str
    ) -> None:
        """
        Validate selected text input.

        Args:
            selected_text: User-selected text
            retrieval_mode: "normal" or "selected_text"

        Raises:
            ValueError: If validation fails
        """
        if retrieval_mode == "selected_text":
            if not selected_text:
                raise ValueError("selected_text is required when retrieval_mode is 'selected_text'")

            if len(selected_text) < 10:
                raise ValueError("selected_text must be at least 10 characters")

            if len(selected_text) > 2000:
                raise ValueError("selected_text must be less than 2000 characters")

    @staticmethod
    def prepare_selected_text_context(
        question: str,
        selected_text: str,
        retrieved_chunks: List[Dict]
    ) -> str:
        """
        Prepare context for selected-text mode.

        Args:
            question: User question
            selected_text: Selected text
            retrieved_chunks: Retrieved chunks (already constrained)

        Returns:
            Formatted context with selection emphasis
        """
        return ContextFormatter.format_selected_text_context(
            selected_text=selected_text,
            chunks=retrieved_chunks
        )

    @staticmethod
    def verify_answer_scope(
        answer: str,
        selected_text: str
    ) -> bool:
        """
        Verify answer focuses on selected text.

        Args:
            answer: Generated answer
            selected_text: User-selected text

        Returns:
            True if answer is appropriately scoped
        """
        # Simple heuristic: answer should reference keywords from selection
        selection_keywords = set(selected_text.lower().split())
        answer_keywords = set(answer.lower().split())

        # Check for keyword overlap
        overlap = selection_keywords.intersection(answer_keywords)
        overlap_ratio = len(overlap) / len(selection_keywords) if selection_keywords else 0

        # Should have at least 30% keyword overlap
        return overlap_ratio >= 0.3
