"""
BookRAGAgent - Main orchestration agent for RAG pipeline.

Orchestrates sub-agents and skills to provide hallucination-free Q&A.
"""

from typing import Optional, Dict, Any, List
import logging
from uuid import UUID
from datetime import datetime

from backend.models.schemas import ChatRequest, ChatResponse, Citation, RetrievedChunkResponse, ChunkMetadata
from backend.agent.sub_agents import RetrievalSubAgent, AnswerSubAgent, GuardrailsSubAgent, SelectionModeSubAgent, MemorySubAgent
from backend.utils.errors import HallucinationDetectedException, RetrievalFailedException

logger = logging.getLogger(__name__)


class BookRAGAgent:
    """Main agent orchestrating the RAG pipeline."""

    def __init__(
        self,
        retrieval_agent: RetrievalSubAgent,
        answer_agent: AnswerSubAgent,
        guardrails_agent: GuardrailsSubAgent,
        selection_mode_agent: Optional[SelectionModeSubAgent] = None,
        memory_agent: Optional[MemorySubAgent] = None
    ):
        """
        Initialize BookRAGAgent.

        Args:
            retrieval_agent: RetrievalSubAgent instance
            answer_agent: AnswerSubAgent instance
            guardrails_agent: GuardrailsSubAgent instance
            selection_mode_agent: Optional SelectionModeSubAgent for selected-text filtering
            memory_agent: Optional MemorySubAgent for multi-turn conversations
        """
        self.retrieval_agent = retrieval_agent
        self.answer_agent = answer_agent
        self.guardrails_agent = guardrails_agent
        self.selection_mode_agent = selection_mode_agent or SelectionModeSubAgent()
        self.memory_agent = memory_agent or MemorySubAgent()

    async def execute(self, chat_request: ChatRequest) -> ChatResponse:
        """
        Execute the RAG pipeline.

        Execution flow:
        1. Retrieve relevant chunks from vector database
        1.5. (Optional) Filter chunks to selected text if provided
        2. Synthesize answer from chunks
        3. Validate answer against chunks (guardrails)
        4. Return grounded answer or fallback message

        Args:
            chat_request: ChatRequest with question, session_id, and optional selected_text

        Returns:
            ChatResponse with answer, citations, and retrieved chunks

        Raises:
            RetrievalFailedException: If retrieval fails
            HallucinationDetectedException: If answer is hallucination
        """
        logger.info(f"BookRAGAgent executing query from session {chat_request.session_id}")

        # Step 0: Retrieve session context for multi-turn awareness
        session_context = None
        try:
            logger.info("Step 0: Retrieving session context...")
            session_context = await self.memory_agent.execute(
                session_id=str(chat_request.session_id)
            )
            if session_context.get("previous_messages"):
                logger.info(f"Retrieved {len(session_context['previous_messages'])} previous messages")
        except Exception as e:
            logger.warning(f"Could not retrieve session context: {e}")
            session_context = {"previous_messages": [], "context_summary": ""}

        try:
            # Step 1: Retrieve chunks
            logger.info("Step 1: Retrieving chunks...")
            chunks = await self.retrieval_agent.execute(
                query_text=chat_request.question
            )

            if not chunks:
                logger.warning("No relevant chunks retrieved")
                return self._build_fallback_response(
                    "I could not find information in the book to answer your question.",
                    []
                )

            # Step 1.5: Apply selected-text filtering if provided
            if chat_request.selected_text:
                logger.info("Step 1.5: Applying selected-text filtering...")
                try:
                    chunks = await self.selection_mode_agent.execute(
                        chunks=chunks,
                        selected_text=chat_request.selected_text
                    )
                except ValueError as e:
                    logger.warning(f"Selected-text filtering failed: {e}")
                    return self._build_fallback_response(
                        "The selected text does not contain relevant information to answer your question.",
                        []
                    )

                if not chunks:
                    logger.warning("No chunks remain after selected-text filtering")
                    return self._build_fallback_response(
                        "The selected text does not contain relevant information to answer your question.",
                        []
                    )

            # Step 2: Synthesize answer
            logger.info("Step 2: Synthesizing answer...")
            answer = await self.answer_agent.execute(
                chunks=chunks,
                query_text=chat_request.question
            )

            # Step 3: Guardrails validation
            logger.info("Step 3: Validating answer against guardrails...")
            guardrail_result = await self.guardrails_agent.execute(
                answer=answer,
                chunks=chunks,
                query_text=chat_request.question
            )

            if not guardrail_result["approved"]:
                logger.warning(f"Answer rejected by guardrails: {guardrail_result.get('veto_reason')}")
                return self._build_fallback_response(
                    "I cannot provide a reliable answer to this question based on the book content.",
                    guardrail_result.get("chunks", [])
                )

            # Step 4: Build response
            logger.info("Building response...")
            return self._build_response(
                answer=guardrail_result["answer"],
                chunks=guardrail_result["chunks"]
            )

        except RetrievalFailedException as e:
            logger.error(f"Retrieval failed: {e}")
            raise
        except HallucinationDetectedException as e:
            logger.error(f"Hallucination detected: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during execution: {e}")
            raise

    def _build_response(
        self,
        answer: str,
        chunks: List[Dict[str, Any]]
    ) -> ChatResponse:
        """
        Build ChatResponse from answer and chunks.

        Args:
            answer: Generated answer
            chunks: Retrieved chunks used in synthesis

        Returns:
            ChatResponse object
        """
        # Build citations from chunks
        citations = []
        seen_sections = set()

        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            section = metadata.get("section", "Unknown Section")
            url = metadata.get("url", "")

            # Avoid duplicate citations
            if section not in seen_sections and url:
                citations.append(Citation(section=section, url=url))
                seen_sections.add(section)

        # Build retrieved chunks response
        retrieved_chunks = []
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            chunk_response = RetrievedChunkResponse(
                text=chunk.get("text", ""),
                metadata=ChunkMetadata(
                    url=metadata.get("url", ""),
                    section=metadata.get("section", ""),
                    chunk_id=metadata.get("chunk_id", ""),
                    position=metadata.get("position", 0),
                    embedding_score=float(metadata.get("embedding_score", 0.0))
                )
            )
            retrieved_chunks.append(chunk_response)

        return ChatResponse(
            answer=answer,
            citations=citations,
            retrieved_chunks=retrieved_chunks
        )

    def _build_fallback_response(
        self,
        message: str,
        chunks: List[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        Build fallback response when no answer can be provided.

        Args:
            message: Fallback message
            chunks: Optional retrieved chunks

        Returns:
            ChatResponse with fallback message
        """
        retrieved_chunks = []

        if chunks:
            for chunk in chunks:
                metadata = chunk.get("metadata", {})
                chunk_response = RetrievedChunkResponse(
                    text=chunk.get("text", ""),
                    metadata=ChunkMetadata(
                        url=metadata.get("url", ""),
                        section=metadata.get("section", ""),
                        chunk_id=metadata.get("chunk_id", ""),
                        position=metadata.get("position", 0),
                        embedding_score=float(metadata.get("embedding_score", 0.0))
                    )
                )
                retrieved_chunks.append(chunk_response)

        return ChatResponse(
            answer=message,
            citations=[],
            retrieved_chunks=retrieved_chunks
        )
