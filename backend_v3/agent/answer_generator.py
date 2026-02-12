"""Answer generation with refusal handling and grounding validation.

Fix:
- Sometimes retrieved_chunks elements come as `str` instead of dict.
  This caused: 'str' object has no attribute 'get'
- We normalize chunks before using `.get()`, so API never crashes.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from backend_v3.agent.gemini_agent import GeminiAgent

# Import Citation from backend models (reuse existing schema)
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend_v3.models import Citation  # noqa: E402


class AnswerGenerator:
    """Generates grounded answers using Gemini agent."""

    def __init__(self, agent: GeminiAgent):
        self.agent = agent

    # -----------------------------
    # Helpers
    # -----------------------------
    def _normalize_chunks(self, retrieved_chunks: Optional[List[Any]]) -> List[Dict[str, Any]]:
        """
        Ensure chunks are always dicts with keys: text, metadata, score.

        Accepts:
        - dict chunk: keep as-is
        - str chunk: convert to {"text": <str>, "metadata": {}, "score": 0.0}
        - anything else: convert to string safely
        """
        if not retrieved_chunks:
            return []

        normalized: List[Dict[str, Any]] = []
        for ch in retrieved_chunks:
            if isinstance(ch, dict):
                normalized.append(ch)
            elif isinstance(ch, str):
                normalized.append({"text": ch, "metadata": {}, "score": 0.0})
            else:
                normalized.append({"text": str(ch), "metadata": {}, "score": 0.0})
        return normalized

    def _normalize_history(self, conversation_history: Optional[List[Any]]) -> List[Dict[str, Any]]:
        """
        Ensure conversation_history always list[dict] so gemini_agent never crashes.
        """
        if not conversation_history:
            return []
        out: List[Dict[str, Any]] = []
        for h in conversation_history:
            if isinstance(h, dict):
                out.append(h)
            else:
                out.append({"question": "", "answer": str(h)})
        return out

    def _is_refusal(self, answer: str) -> bool:
        refusal_phrases = [
            "i cannot answer this question based on the provided context",
            "cannot answer",
            "not in the context",
            "not found in the book",
            "information is not present",
            "don't have enough information",
            "not provided in the context",
        ]
        answer_lower = (answer or "").lower()
        return any(phrase in answer_lower for phrase in refusal_phrases)

    # -----------------------------
    # Main API
    # -----------------------------
    def generate_answer(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Generate grounded answer.

        Returns:
            Dict with answer, grounded flag, refusal info
        """
        safe_history = self._normalize_history(conversation_history)

        answer = self.agent.create_chat_completion(
            question=question,
            context=context,
            conversation_history=safe_history,
        )

        is_refusal = self._is_refusal(answer)

        return {
            "answer": answer,
            "grounded": True,  # validation happens separately (route can override)
            "is_refusal": is_refusal,
        }

    def extract_citations(self, answer: str, retrieved_chunks: List[Any]) -> List[Citation]:
        """
        Extract citations from retrieved chunks.
        """
        chunks = self._normalize_chunks(retrieved_chunks)
        citations: List[Citation] = []

        # If refusal OR no chunks => empty citations
        if self._is_refusal(answer) or not chunks:
            return citations

        # Take top 3 chunks as citations
        for chunk in chunks[:3]:
            metadata = chunk.get("metadata") or {}
            text = chunk.get("text") or ""

            citations.append(
                Citation(
                    chapter=metadata.get("chapter", "Unknown"),
                    section=metadata.get("section", "Unknown"),
                    text_snippet=(text[:150] + "...") if len(text) > 150 else text,
                    score=float(chunk.get("score", 0.0) or 0.0),
                )
            )

        return citations

    def validate_grounding(self, answer: str, retrieved_chunks: List[Any]) -> bool:
        """
        Validate that answer is grounded in chunks.

        - Refusals are grounded (no claims to verify)
        - Otherwise, keyword overlap heuristic
        """
        if self._is_refusal(answer):
            return True

        chunks = self._normalize_chunks(retrieved_chunks)
        if not chunks:
            return False

        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "is", "are", "was", "were",
            "this", "that", "it", "as", "be", "been", "being",
        }

        # Keywords from answer
        answer_keywords = set(
            w.lower().strip(".,:;!?()[]{}\"'")
            for w in (answer or "").split()
            if len(w) > 3 and w.lower() not in stop_words
        )
        if not answer_keywords:
            return True

        # Keywords from chunks
        chunk_keywords = set()
        for chunk in chunks:
            chunk_text = (chunk.get("text") or "").lower()
            for w in chunk_text.split():
                w = w.strip(".,:;!?()[]{}\"'")
                if len(w) > 3 and w not in stop_words:
                    chunk_keywords.add(w)

        if not chunk_keywords:
            return False

        overlap = answer_keywords.intersection(chunk_keywords)
        overlap_ratio = len(overlap) / max(1, len(answer_keywords))

        # 60% overlap threshold
        return overlap_ratio >= 0.6
