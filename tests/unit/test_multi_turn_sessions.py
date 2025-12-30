"""
Unit tests for Multi-Turn Sessions (Phase 5).

Tests the multi-turn conversation capabilities and session persistence.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from backend.models.schemas import ChatRequest, ChatResponse
from backend.agent.sub_agents import MemorySubAgent
from backend.rag.grounding import SessionPersistenceSkill
from backend.agent.agent import BookRAGAgent


@pytest.fixture
def session_persistence_skill():
    """Create SessionPersistenceSkill instance."""
    return SessionPersistenceSkill()


@pytest.fixture
def memory_agent():
    """Create MemorySubAgent instance."""
    return MemorySubAgent()


@pytest.fixture
def session_id():
    """Generate a session ID."""
    return uuid4()


class TestSessionPersistenceSkill:
    """Test cases for SessionPersistenceSkill."""

    @pytest.mark.asyncio
    async def test_execute_no_session_manager(self, session_persistence_skill, session_id):
        """Test skill returns empty context when no session manager provided."""
        result = await session_persistence_skill.execute(session_id=str(session_id))

        assert result["session_id"] == str(session_id)
        assert result["previous_messages"] == []
        assert result["context_summary"] == ""

    @pytest.mark.asyncio
    async def test_execute_with_mock_session_manager(self, session_id):
        """Test skill returns context with mock session manager."""
        # Create mock session manager
        mock_session_manager = MagicMock()
        mock_session_manager.get_session = MagicMock(return_value=MagicMock())
        mock_session_manager.get_messages = MagicMock(return_value=[])

        skill = SessionPersistenceSkill(session_manager=mock_session_manager)
        result = await skill.execute(session_id=str(session_id))

        assert result["session_id"] == str(session_id)
        assert result["previous_messages"] == []
        assert result["context_summary"] == ""


class TestMemorySubAgent:
    """Test cases for MemorySubAgent."""

    @pytest.mark.asyncio
    async def test_execute_without_persistence_skill(self, memory_agent, session_id):
        """Test memory agent executes without skill (lazy initialization)."""
        result = await memory_agent.execute(session_id=str(session_id))

        assert result["session_id"] == str(session_id)
        assert "previous_messages" in result
        assert "context_summary" in result

    @pytest.mark.asyncio
    async def test_execute_with_mock_skill(self, session_id):
        """Test memory agent with mocked persistence skill."""
        mock_skill = AsyncMock()
        mock_skill.execute = AsyncMock(return_value={
            "session_id": str(session_id),
            "previous_messages": [
                "user: What is neural networks?",
                "assistant: Neural networks are..."
            ],
            "context_summary": "Discussed neural networks basics"
        })

        agent = MemorySubAgent(persistence_skill=mock_skill)
        result = await agent.execute(session_id=str(session_id))

        assert result["session_id"] == str(session_id)
        assert len(result["previous_messages"]) == 2
        assert "neural networks" in result["context_summary"].lower()

    @pytest.mark.asyncio
    async def test_execute_empty_session(self, memory_agent, session_id):
        """Test memory agent returns empty context for new session."""
        result = await memory_agent.execute(session_id=str(session_id))

        assert result["session_id"] == str(session_id)
        assert isinstance(result["previous_messages"], list)


class TestMultiTurnConversation:
    """Integration tests for multi-turn conversations."""

    @pytest.mark.asyncio
    async def test_agent_with_memory_integration(self, session_id):
        """Test BookRAGAgent with memory sub-agent integration."""
        # Mock sub-agents
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()
        memory_agent = AsyncMock()

        # Mock memory context
        memory_agent.execute = AsyncMock(return_value={
            "session_id": str(session_id),
            "previous_messages": [
                "user: What is neural networks?",
                "assistant: Neural networks are computational models..."
            ],
            "context_summary": "Previous discussion on neural networks"
        })

        # Mock retrieval and synthesis
        sample_chunks = [
            {
                "text": "Chapter 3 covers neural networks",
                "metadata": {
                    "url": "https://example.com/chapter-3",
                    "section": "Chapter 3",
                    "chunk_id": "chunk-042",
                    "position": 1,
                    "embedding_score": 0.87
                }
            }
        ]

        retrieval_agent.execute = AsyncMock(return_value=sample_chunks)
        answer_agent.execute = AsyncMock(return_value="Continuing from our discussion, RNNs are...")
        guardrails_agent.execute = AsyncMock(return_value={
            "approved": True,
            "answer": "Continuing from our discussion, RNNs are...",
            "chunks": sample_chunks
        })

        # Create agent with memory
        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent,
            memory_agent=memory_agent
        )

        # Create second turn request
        request = ChatRequest(
            question="What about RNNs?",
            session_id=session_id,
            selected_text=None
        )

        # Execute
        response = await agent.execute(request)

        # Verify memory agent was called
        memory_agent.execute.assert_called_once()
        assert isinstance(response, ChatResponse)
        assert response.answer is not None

    @pytest.mark.asyncio
    async def test_multi_turn_without_previous_messages(self, session_id):
        """Test multi-turn conversation when session is new."""
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()
        memory_agent = AsyncMock()

        # Mock empty session
        memory_agent.execute = AsyncMock(return_value={
            "session_id": str(session_id),
            "previous_messages": [],
            "context_summary": ""
        })

        sample_chunks = [
            {
                "text": "Chapter 1 introduces basics",
                "metadata": {
                    "url": "https://example.com/chapter-1",
                    "section": "Chapter 1",
                    "chunk_id": "chunk-001",
                    "position": 1,
                    "embedding_score": 0.90
                }
            }
        ]

        retrieval_agent.execute = AsyncMock(return_value=sample_chunks)
        answer_agent.execute = AsyncMock(return_value="Chapter 1 introduces...")
        guardrails_agent.execute = AsyncMock(return_value={
            "approved": True,
            "answer": "Chapter 1 introduces...",
            "chunks": sample_chunks
        })

        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent,
            memory_agent=memory_agent
        )

        request = ChatRequest(
            question="What are the basics?",
            session_id=session_id
        )

        response = await agent.execute(request)

        # Should still work fine with new session
        assert isinstance(response, ChatResponse)
        assert response.answer is not None

    @pytest.mark.asyncio
    async def test_session_context_does_not_affect_retrieval(self):
        """Test that session context doesn't become RAG source."""
        session_id = uuid4()

        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()
        memory_agent = AsyncMock()

        # Memory agent returns context with some information
        memory_agent.execute = AsyncMock(return_value={
            "session_id": str(session_id),
            "previous_messages": [
                "user: Tell me about quantum computing",
                "assistant: Quantum computing uses quantum bits..."
            ],
            "context_summary": "Previously discussed quantum computing"
        })

        # But retrieval returns something different
        sample_chunks = [
            {
                "text": "Neural networks use backpropagation",
                "metadata": {
                    "url": "https://example.com/nn",
                    "section": "Neural Networks",
                    "chunk_id": "chunk-100",
                    "position": 1,
                    "embedding_score": 0.85
                }
            }
        ]

        retrieval_agent.execute = AsyncMock(return_value=sample_chunks)
        answer_agent.execute = AsyncMock(return_value="Neural networks use backpropagation...")
        guardrails_agent.execute = AsyncMock(return_value={
            "approved": True,
            "answer": "Neural networks use backpropagation...",
            "chunks": sample_chunks
        })

        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent,
            memory_agent=memory_agent
        )

        request = ChatRequest(
            question="Tell me about neural networks",
            session_id=session_id
        )

        response = await agent.execute(request)

        # Answer should be from retrieval (neural networks), not memory (quantum)
        assert "neural networks" in response.answer.lower()
        assert "quantum" not in response.answer.lower()
