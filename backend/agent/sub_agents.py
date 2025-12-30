"""
Sub-agents for BookRAGAgent orchestration.

Each sub-agent handles a specific part of the RAG pipeline:
- RetrievalSubAgent: Retrieves relevant chunks
- AnswerSubAgent: Synthesizes answer from chunks
- GuardrailsSubAgent: Validates answer and detects hallucinations
"""

from typing import List, Dict, Any, Optional
import logging

from backend.rag.retrieval import VectorSearchSkill
from backend.rag.grounding import GroundedSynthesisSkill, AntiHallucinationSkill, RetrievalValidationSkill
from backend.services.openrouter_service import OpenRouterClient

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
            Synthesized answer
        """
        logger.info(f"AnswerSubAgent synthesizing answer from {len(chunks)} chunks")

        answer = await self.synthesis_skill.execute(
            chunks=chunks,
            query_text=query_text
        )

        logger.info(f"AnswerSubAgent generated answer: {answer[:50]}...")
        return answer


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
        """
        logger.info("GuardrailsSubAgent validating answer")

        # Validate chunk metadata
        try:
            validated_chunks = await self.validation_skill.execute(chunks)
        except Exception as e:
            logger.error(f"Chunk validation failed: {e}")
            validated_chunks = chunks

        # Check for hallucinations
        hallucination_check = await self.hallucination_skill.execute(
            answer=answer,
            chunks=validated_chunks,
            query_text=query_text
        )

        if hallucination_check["grounded"]:
            logger.info("Answer approved by guardrails")
            return {
                "approved": True,
                "answer": answer,
                "chunks": validated_chunks
            }
        else:
            logger.warning(f"Answer vetoed: {hallucination_check.get('veto_reason', 'Unknown reason')}")
            return {
                "approved": False,
                "veto_reason": hallucination_check.get("veto_reason", "Unknown reason"),
                "chunks": validated_chunks
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
                from backend.rag.grounding import SelectedTextOverrideSkill
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
