"""
Grounding and hallucination detection skills for RAG pipeline.

Provides skills for synthesizing answers from chunks and detecting hallucinations.
"""

from typing import List, Dict, Any, Optional
import logging
import json

from backend.agent.skills import Skill
from backend.services.openrouter_service import OpenRouterClient

logger = logging.getLogger(__name__)


class GroundedSynthesisSkill(Skill):
    """Skill for synthesizing answers exclusively from retrieved chunks."""

    def __init__(self, llm_client: OpenRouterClient):
        """
        Initialize GroundedSynthesisSkill.

        Args:
            llm_client: OpenRouterClient instance
        """
        super().__init__("GroundedSynthesisSkill")
        self.llm_client = llm_client

    async def execute(
        self,
        chunks: List[Dict[str, Any]],
        query_text: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Synthesize an answer from chunks.

        Args:
            chunks: Retrieved chunks with metadata
            query_text: Original user query
            temperature: LLM temperature
            max_tokens: Maximum tokens in response

        Returns:
            Synthesized answer
        """
        try:
            if not chunks:
                return "I could not find relevant information to answer your question."

            # Build context from chunks
            chunk_texts = "\n\n".join([
                f"[{chunk['metadata']['chunk_id']}] {chunk['text']}"
                for chunk in chunks
            ])

            # Create prompt that enforces grounding
            prompt = f"""You are a helpful assistant answering questions about a book based on provided excerpts.

IMPORTANT: You MUST answer ONLY based on the following book excerpts. Do not use external knowledge.
If the excerpts don't contain enough information to answer, say so explicitly.

Book Excerpts:
{chunk_texts}

User Question: {query_text}

Provide a clear, concise answer based ONLY on the excerpts above."""

            logger.info(f"Synthesizing answer from {len(chunks)} chunks")

            # Call LLM
            result = await self.llm_client.call(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            answer = result["content"]
            logger.info(f"Generated answer: {answer[:100]}...")
            return answer

        except Exception as e:
            logger.error(f"Answer synthesis failed: {e}")
            raise


class AntiHallucinationSkill(Skill):
    """Skill for detecting and vetoing hallucinations."""

    def __init__(self, llm_client: OpenRouterClient):
        """
        Initialize AntiHallucinationSkill.

        Args:
            llm_client: OpenRouterClient instance
        """
        super().__init__("AntiHallucinationSkill")
        self.llm_client = llm_client

    async def execute(
        self,
        answer: str,
        chunks: List[Dict[str, Any]],
        query_text: str
    ) -> Dict[str, Any]:
        """
        Validate answer against chunks for hallucinations.

        Args:
            answer: Generated answer to validate
            chunks: Original retrieved chunks
            query_text: Original user query

        Returns:
            Dictionary with 'grounded' (bool) and optionally 'veto_reason' (str)
        """
        try:
            # Build chunk text for reference
            chunk_texts = "\n\n".join([
                f"[{chunk['metadata']['chunk_id']}] {chunk['text']}"
                for chunk in chunks
            ])

            # Create validation prompt
            prompt = f"""You are a fact-checker for a book Q&A system.

Your task: Determine if the answer is grounded ONLY in the provided book excerpts.

Book Excerpts:
{chunk_texts}

User Question: {query_text}

Generated Answer:
{answer}

Respond with ONLY one word:
- "GROUNDED" if the answer is fully supported by the excerpts
- "HALLUCINATION" if the answer contains information not in the excerpts or is partially fabricated"""

            logger.info("Checking answer for hallucinations")

            # Call LLM for validation
            result = await self.llm_client.call(
                prompt=prompt,
                temperature=0.0,  # Deterministic
                max_tokens=50
            )

            validation = result["content"].strip().upper()

            if "GROUNDED" in validation:
                logger.info("Answer passed hallucination check")
                return {"grounded": True}
            else:
                logger.warning("Hallucination detected in answer")
                return {
                    "grounded": False,
                    "veto_reason": "Answer contains information not supported by the source material."
                }

        except Exception as e:
            logger.error(f"Hallucination check failed: {e}")
            # Default to safe response
            return {
                "grounded": False,
                "veto_reason": "Could not validate answer against source material."
            }


class RetrievalValidationSkill(Skill):
    """Skill for validating metadata integrity of retrieved chunks."""

    def __init__(self):
        """Initialize RetrievalValidationSkill."""
        super().__init__("RetrievalValidationSkill")

    async def execute(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate chunk metadata integrity.

        Args:
            chunks: Retrieved chunks to validate

        Returns:
            Cleaned/validated chunks

        Raises:
            ValueError: If validation fails critically
        """
        try:
            if not chunks:
                logger.warning("No chunks to validate")
                return []

            validated_chunks = []

            for chunk in chunks:
                # Check required fields
                if "text" not in chunk or not chunk["text"]:
                    logger.warning(f"Chunk missing text field: {chunk}")
                    continue

                if "metadata" not in chunk:
                    logger.warning(f"Chunk missing metadata: {chunk}")
                    continue

                metadata = chunk["metadata"]

                # Validate required metadata fields
                required_fields = ["chunk_id", "section", "url"]
                if not all(field in metadata for field in required_fields):
                    logger.warning(f"Chunk missing required metadata fields: {chunk}")
                    continue

                # Validate embedding score
                if "embedding_score" in metadata:
                    score = metadata["embedding_score"]
                    if not (0 <= score <= 1):
                        logger.warning(f"Invalid embedding score: {score}")
                        metadata["embedding_score"] = max(0, min(1, score))  # Clamp

                validated_chunks.append(chunk)

            logger.info(f"Validated {len(validated_chunks)} / {len(chunks)} chunks")
            return validated_chunks

        except Exception as e:
            logger.error(f"Chunk validation failed: {e}")
            raise


class SelectedTextOverrideSkill(Skill):
    """Skill for filtering chunks to only those within selected text."""

    def __init__(self):
        """Initialize SelectedTextOverrideSkill."""
        super().__init__("SelectedTextOverrideSkill")

    async def execute(self, chunks: List[Dict[str, Any]], selected_text: str) -> List[Dict[str, Any]]:
        """
        Filter chunks to only those that overlap with selected text.

        When a user selects specific text, restrict the answer to ONLY
        information from that passage. This is the "selected-text mode".

        Args:
            chunks: Retrieved chunks from vector search
            selected_text: User-selected passage to restrict to

        Returns:
            Filtered chunks that overlap with selected text

        Raises:
            ValueError: If no chunks overlap with selected text
        """
        try:
            if not selected_text or not selected_text.strip():
                logger.warning("Empty selected_text provided, returning all chunks")
                return chunks

            if not chunks:
                logger.warning("No chunks to filter")
                return []

            # Normalize selected text for matching
            selected_lower = selected_text.strip().lower()

            filtered_chunks = []

            for chunk in chunks:
                chunk_text = chunk.get("text", "").lower()

                # Check if this chunk overlaps with selected text
                # We use substring matching as a heuristic for overlap
                if selected_lower in chunk_text or chunk_text in selected_lower:
                    filtered_chunks.append(chunk)
                    logger.debug(f"Chunk {chunk['metadata']['chunk_id']} overlaps with selected text")
                else:
                    # Also check if significant portions of selected text appear in chunk
                    # This helps catch partial overlaps
                    words = selected_lower.split()
                    if len(words) > 0 and sum(1 for word in words if word in chunk_text) > len(words) * 0.7:
                        filtered_chunks.append(chunk)
                        logger.debug(f"Chunk {chunk['metadata']['chunk_id']} has significant overlap with selected text")

            if not filtered_chunks:
                logger.warning(f"No chunks matched selected text: '{selected_text[:100]}...'")
                raise ValueError(
                    "The selected text does not match any retrieved chunks. "
                    "Please select text that appears in the book."
                )

            logger.info(f"Filtered {len(filtered_chunks)} / {len(chunks)} chunks for selected-text mode")
            return filtered_chunks

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Selected text filtering failed: {e}")
            raise ValueError(f"Failed to filter chunks for selected text: {e}")


class SessionPersistenceSkill(Skill):
    """Skill for retrieving and using session context for multi-turn conversations."""

    def __init__(self, session_manager=None):
        """
        Initialize SessionPersistenceSkill.

        Args:
            session_manager: SessionManager instance for retrieving session history
        """
        super().__init__("SessionPersistenceSkill")
        self.session_manager = session_manager

    async def execute(
        self,
        session_id: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve session context from conversation history.

        Retrieves previous messages in the session to provide context
        for multi-turn conversations without contaminating the RAG retrieval.

        Args:
            session_id: UUID of the conversation session
            limit: Maximum number of previous messages to retrieve

        Returns:
            Dictionary with session context:
            {
                "session_id": session_id,
                "previous_messages": [...],
                "context_summary": "summary of previous conversation"
            }

        Raises:
            ValueError: If session not found
        """
        try:
            if not self.session_manager:
                logger.warning("No session manager provided, returning empty context")
                return {
                    "session_id": str(session_id),
                    "previous_messages": [],
                    "context_summary": ""
                }

            # Get session
            try:
                session = self.session_manager.get_session(session_id)
            except Exception as e:
                logger.warning(f"Could not retrieve session {session_id}: {e}")
                return {
                    "session_id": str(session_id),
                    "previous_messages": [],
                    "context_summary": ""
                }

            # Get recent messages (excluding current turn)
            messages = self.session_manager.get_messages(session_id, limit=limit)

            if not messages:
                logger.info(f"No previous messages in session {session_id}")
                return {
                    "session_id": str(session_id),
                    "previous_messages": [],
                    "context_summary": ""
                }

            # Build context summary
            message_texts = [f"{msg.role}: {msg.content}" for msg in messages]
            context_summary = "\n".join(message_texts[-limit:])

            logger.info(f"Retrieved {len(messages)} messages from session {session_id}")

            return {
                "session_id": str(session_id),
                "previous_messages": message_texts[-limit:],
                "context_summary": context_summary,
                "message_count": len(messages)
            }

        except Exception as e:
            logger.error(f"Session persistence skill failed: {e}")
            return {
                "session_id": str(session_id),
                "previous_messages": [],
                "context_summary": ""
            }
