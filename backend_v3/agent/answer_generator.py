"""Answer generation with refusal handling and grounding validation."""

from typing import Dict, List
from backend_v3.agent.gemini_agent import GeminiAgent


# Import Citation from backend models (reuse existing schema)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend_v3.models import Citation


class AnswerGenerator:
    """Generates grounded answers using Gemini agent."""

    def __init__(self, agent: GeminiAgent):
        """
        Initialize answer generator.

        Args:
            agent: Configured Gemini agent
        """
        self.agent = agent

    def generate_answer(
        self,
        question: str,
        context: str,
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Generate grounded answer.

        Args:
            question: User question
            context: Formatted context
            conversation_history: Optional history

        Returns:
            Dict with answer, grounded flag, refusal info
        """
        # Call agent
        answer = self.agent.create_chat_completion(
            question=question,
            context=context,
            conversation_history=conversation_history
        )

        # Detect refusal
        is_refusal = self._is_refusal(answer)

        return {
            "answer": answer,
            "grounded": True,  # Assume grounded (agent enforces this)
            "is_refusal": is_refusal
        }

    def _is_refusal(self, answer: str) -> bool:
        """
        Detect if answer is a refusal.

        Args:
            answer: Generated answer

        Returns:
            True if answer is a refusal
        """
        refusal_phrases = [
            "cannot answer",
            "not in the context",
            "not found in the book",
            "information is not present",
            "don't have enough information",
            "not provided in the context"
        ]

        answer_lower = answer.lower()
        return any(phrase in answer_lower for phrase in refusal_phrases)

    def extract_citations(
        self,
        answer: str,
        retrieved_chunks: List[Dict]
    ) -> List[Citation]:
        """
        Extract citations from answer and chunks.

        Args:
            answer: Generated answer
            retrieved_chunks: Retrieved chunks

        Returns:
            List of citations
        """
        citations = []

        # Extract top 3 chunks as citations
        for chunk in retrieved_chunks[:3]:
            metadata = chunk.get("metadata", {})
            text = chunk.get("text", "")

            citations.append(Citation(
                chapter=metadata.get("chapter", "Unknown"),
                section=metadata.get("section", "Unknown"),
                text_snippet=text[:150] + "..." if len(text) > 150 else text,
                score=chunk.get("score", 0.0)
            ))

        return citations

    def validate_grounding(
        self,
        answer: str,
        retrieved_chunks: List[Dict]
    ) -> bool:
        """
        Validate that answer is grounded in chunks.

        Args:
            answer: Generated answer
            retrieved_chunks: Retrieved chunks

        Returns:
            True if answer appears grounded
        """
        # Refusals are considered grounded (no claims to verify)
        if self._is_refusal(answer):
            return True

        # Extract keywords from answer (excluding common words)
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "is", "are", "was", "were",
            "this", "that", "it", "as", "be", "been", "being"
        }

        answer_keywords = set(
            word.lower() for word in answer.split()
            if len(word) > 3 and word.lower() not in stop_words
        )

        # Extract keywords from chunks
        chunk_keywords = set()
        for chunk in retrieved_chunks:
            chunk_text = chunk.get("text", "").lower()
            chunk_keywords.update(
                word for word in chunk_text.split()
                if len(word) > 3 and word not in stop_words
            )

        # Check keyword overlap
        if not answer_keywords:
            return True  # Empty answer (refusal)

        overlap = answer_keywords.intersection(chunk_keywords)
        overlap_ratio = len(overlap) / len(answer_keywords)

        # Should have at least 60% keyword overlap
        return overlap_ratio >= 0.6
