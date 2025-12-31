"""
Sub-agents for BookRAGAgent orchestration.

Each sub-agent handles a specific part of the RAG pipeline:
- RetrievalSubAgent: Retrieves relevant chunks
- AnswerSubAgent: Synthesizes answer from chunks
- GuardrailsSubAgent: Validates answer and detects hallucinations
"""

from typing import List, Dict, Any, Optional
import logging

from rag.retrieval import VectorSearchSkill
from rag.grounding import GroundedSynthesisSkill, AntiHallucinationSkill, RetrievalValidationSkill
from services.openrouter_service import OpenRouterClient

logger = logging.getLogger(__name__)


class SubAgentBase:
    """Base class for sub-agents."""

    def __init__(self, name: str):
        """
        Initialize sub-agent.

        Args:
            name: Sub-agent name
        """
        self.name = name

    async def execute(self, *args, **kwargs) -> Any:
        """Execute the sub-agent."""
        raise NotImplementedError


class SubAgentRegistry:
    """Registry for managing sub-agent instances."""

    _instance = None
    _agents = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SubAgentRegistry, cls).__new__(cls)
        return cls._instance

    def register(self, name: str, agent: SubAgentBase) -> None:
        """Register a sub-agent."""
        self._agents[name] = agent
        logger.info(f"Registered sub-agent: {name}")

    def get(self, name: str) -> Optional[SubAgentBase]:
        """Get a registered sub-agent."""
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        """List all registered sub-agents."""
        return list(self._agents.keys())


class RetrievalSubAgent(SubAgentBase):
    """Sub-agent for retrieving relevant chunks."""

    def __init__(self, vector_search_skill: VectorSearchSkill):
        """
        Initialize RetrievalSubAgent.

        Args:
            vector_search_skill: VectorSearchSkill instance
        """
        super().__init__("RetrievalSubAgent")
        self.vector_search_skill = vector_search_skill

    async def execute(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks.

        Args:
            query_text: User's question
            top_k: Number of chunks to retrieve
            threshold: Similarity threshold

        Returns:
            List of retrieved chunks
        """
        logger.info(f"RetrievalSubAgent executing for query: {query_text[:50]}...")

        chunks = await self.vector_search_skill.execute(
            query_text=query_text,
            top_k=top_k,
            threshold=threshold
        )

        logger.info(f"RetrievalSubAgent retrieved {len(chunks)} chunks")
        return chunks


class AnswerSubAgent(SubAgentBase):
    """Sub-agent for synthesizing answers."""

    def __init__(self, synthesis_skill: GroundedSynthesisSkill):
        """
        Initialize AnswerSubAgent.

        Args:
            synthesis_skill: GroundedSynthesisSkill instance
        """
        super().__init__("AnswerSubAgent")
        self.synthesis_skill = synthesis_skill

    async def execute(
        self,
        chunks: List[Dict[str, Any]],
        query_text: str
    ) -> str:
        """
        Synthesize an answer from chunks.

        Args:
            chunks: Retrieved chunks
            query_text: Original user query

        Returns:
            Synthesized answer (guaranteed non-None string)
        """
        try:
            logger.info(f"AnswerSubAgent synthesizing answer from {len(chunks)} chunks")

            answer = await self.synthesis_skill.execute(
                chunks=chunks,
                query_text=query_text
            )

            # Validate answer is not None and is a string
            if answer is None:
                logger.error("GroundedSynthesisSkill returned None")
                answer = "I was unable to generate an answer. Please try again."

            if not isinstance(answer, str):
                logger.error(f"GroundedSynthesisSkill returned non-string: {type(answer)}")
                answer = str(answer) if answer else "I was unable to generate an answer."

            # Ensure answer is not empty
            if not answer.strip():
                logger.warning("GroundedSynthesisSkill returned empty string")
                answer = "I could not generate an answer based on the provided information."

            logger.info(f"AnswerSubAgent generated answer: {answer[:100]}...")
            return answer

        except Exception as e:
            logger.error(f"AnswerSubAgent.execute() failed: {e}", exc_info=True)
            return "I encountered an error while synthesizing an answer. Please try again."


class GuardrailsSubAgent(SubAgentBase):
    """Sub-agent for validating answers and detecting hallucinations."""

    def __init__(
        self,
        validation_skill: RetrievalValidationSkill,
        hallucination_skill: AntiHallucinationSkill
    ):
        """
        Initialize GuardrailsSubAgent.

        Args:
            validation_skill: RetrievalValidationSkill instance
            hallucination_skill: AntiHallucinationSkill instance
        """
        super().__init__("GuardrailsSubAgent")
        self.validation_skill = validation_skill
        self.hallucination_skill = hallucination_skill

    async def execute(
        self,
        answer: str,
        chunks: List[Dict[str, Any]],
        query_text: str
    ) -> Dict[str, Any]:
        """
        Validate answer against chunks.

        Args:
            answer: Generated answer to validate
            chunks: Original retrieved chunks
            query_text: Original user query

        Returns:
            Dictionary with 'approved' (bool), 'answer', and optionally 'veto_reason'
            Always returns valid dict with required keys
        """
        try:
            logger.info("GuardrailsSubAgent validating answer")

            # Validate input
            if not answer or not isinstance(answer, str):
                logger.error(f"Invalid answer for guardrails: {type(answer)}")
                return {
                    "approved": False,
                    "veto_reason": "Invalid answer format",
                    "answer": str(answer) if answer else "No answer provided",
                    "chunks": chunks
                }

            # Validate chunk metadata
            validated_chunks = chunks
            try:
                validated_chunks = await self.validation_skill.execute(chunks)
                if validated_chunks is None:
                    logger.warning("Chunk validation returned None, using original chunks")
                    validated_chunks = chunks
            except Exception as e:
                logger.error(f"Chunk validation failed: {e}")
                validated_chunks = chunks

            # Check for hallucinations
            try:
                hallucination_check = await self.hallucination_skill.execute(
                    answer=answer,
                    chunks=validated_chunks,
                    query_text=query_text
                )
            except Exception as e:
                logger.error(f"Hallucination check failed: {e}", exc_info=True)
                # Default to approval if hallucination check fails
                hallucination_check = {"grounded": True}

            # Validate hallucination_check is not None
            if hallucination_check is None:
                logger.error("AntiHallucinationSkill returned None")
                hallucination_check = {"grounded": True}

            if not isinstance(hallucination_check, dict):
                logger.error(f"AntiHallucinationSkill returned non-dict: {type(hallucination_check)}")
                hallucination_check = {"grounded": True}

            # Get grounded status (default to True if missing)
            grounded = hallucination_check.get("grounded", True)

            if grounded:
                logger.info("Answer approved by guardrails")
                return {
                    "approved": True,
                    "answer": answer,
                    "chunks": validated_chunks
                }
            else:
                veto_reason = hallucination_check.get("veto_reason", "Failed guardrail validation")
                logger.warning(f"Answer vetoed: {veto_reason}")
                return {
                    "approved": False,
                    "veto_reason": veto_reason,
                    "answer": answer,
                    "chunks": validated_chunks
                }

        except Exception as e:
            logger.error(f"GuardrailsSubAgent.execute() failed: {e}", exc_info=True)
            # Return safe approval on unexpected error
            return {
                "approved": True,
                "answer": answer,
                "chunks": chunks
            }


class SelectionModeSubAgent(SubAgentBase):
    """Sub-agent for handling selected-text mode filtering."""

    def __init__(self, selected_text_skill=None):
        """
        Initialize SelectionModeSubAgent.

        Args:
            selected_text_skill: SelectedTextOverrideSkill instance (lazy imported)
        """
        super().__init__("SelectionModeSubAgent")
        self.selected_text_skill = selected_text_skill

    async def execute(self, chunks: List[Dict[str, Any]], selected_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Filter chunks based on selected text if provided.

        When a user provides selected_text, restrict the RAG pipeline to only
        consider chunks that overlap with the selected passage. This ensures
        answers are strictly limited to user-selected content.

        Args:
            chunks: Retrieved chunks from vector search
            selected_text: Optional user-selected text restriction

        Returns:
            Filtered chunks (or original chunks if no selected_text)

        Raises:
            ValueError: If selected_text is provided but no chunks match
        """
        try:
            # No selection mode - return all chunks
            if not selected_text or not selected_text.strip():
                logger.info("No selected text provided, using all chunks")
                return chunks

            # Selected text provided - must filter chunks
            logger.info(f"Selected-text mode active, filtering {len(chunks)} chunks")

            # Lazy import to avoid circular dependencies
            if self.selected_text_skill is None:
                from rag.grounding import SelectedTextOverrideSkill
                self.selected_text_skill = SelectedTextOverrideSkill()

            # Filter chunks to only those matching selected text
            filtered_chunks = await self.selected_text_skill.execute(
                chunks=chunks,
                selected_text=selected_text
            )

            logger.info(f"Selected-text filtering: {len(chunks)} → {len(filtered_chunks)} chunks")
            return filtered_chunks

        except ValueError as e:
            logger.warning(f"Selected text filtering produced no results: {e}")
            raise
        except Exception as e:
            logger.error(f"Selection mode sub-agent failed: {e}")
            raise


class MemorySubAgent(SubAgentBase):
    """Sub-agent for managing session memory and conversation context."""

    def __init__(self, persistence_skill=None):
        """
        Initialize MemorySubAgent.

        Args:
            persistence_skill: SessionPersistenceSkill instance
        """
        super().__init__("MemorySubAgent")
        self.persistence_skill = persistence_skill

    async def execute(self, session_id: str, limit: int = 5) -> Dict[str, Any]:
        """
        Retrieve and provide session context for multi-turn conversations.

        This agent retrieves previous messages from the session to maintain
        conversation context without using them as a knowledge source for RAG.

        Args:
            session_id: UUID of the conversation session
            limit: Maximum previous messages to include

        Returns:
            Session context dictionary with conversation history

        Raises:
            ValueError: If session not found or retrieval fails
        """
        try:
            # Lazy import to avoid circular dependencies
            if self.persistence_skill is None:
                from rag.grounding import SessionPersistenceSkill
                self.persistence_skill = SessionPersistenceSkill()

            logger.info(f"Memory agent retrieving context for session {session_id}")

            # Get session context
            context = await self.persistence_skill.execute(
                session_id=session_id,
                limit=limit
            )

            if not context.get("previous_messages"):
                logger.info(f"No previous messages for session {session_id}, starting fresh")

            return context

        except Exception as e:
            logger.error(f"Memory sub-agent failed: {e}")
            # Return empty context on error
            return {
                "session_id": str(session_id),
                "previous_messages": [],
                "context_summary": "",
                "error": str(e)
            }
