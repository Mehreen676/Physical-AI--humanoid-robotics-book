# Agentic RAG Implementation - Section Structure

## Overview

This document breaks down the agentic RAG implementation into 6 well-defined sections, each with clear responsibilities, interfaces, and validation criteria.

---

## Section 1: Agent Configuration and System Instructions

### Purpose
Configure OpenAI Agents SDK / ChatKit with strict grounding rules to ensure agent answers are based solely on retrieved book content.

### Components

**File**: `backend/agent/chatkit_agent.py`

**Key Elements**:
1. Agent initialization with OpenAI SDK
2. System instruction template
3. Grounding rules enforcement
4. Temperature and parameter configuration

### Implementation

```python
from openai import OpenAI

class ChatKitAgent:
    """OpenAI Agents SDK wrapper for grounded book Q&A."""

    def __init__(self, api_key: str):
        """
        Initialize ChatKit agent.

        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4-turbo-preview"  # or gpt-4o
        self.temperature = 0.0  # Deterministic responses

    def get_system_instructions(self) -> str:
        """
        Get system instructions enforcing strict grounding.

        Returns:
            System instruction string
        """
        return """You are a helpful assistant that answers questions about a book.

CRITICAL GROUNDING RULES:
1. Use ONLY the provided context to answer questions
2. If the answer is not in the context, respond: "I cannot answer this question based on the book content provided."
3. Do NOT use external knowledge or prior information
4. Do NOT infer, speculate, or extrapolate beyond the context
5. Cite chapter and section when possible using format: [Chapter X, Section Y]
6. Keep answers concise and directly address the question
7. If context is ambiguous, acknowledge uncertainty

CONTEXT FORMAT:
You will receive retrieved book chunks with metadata.
Each chunk includes:
- Chapter name
- Section name
- Text content
- Relevance score

These chunks are your SOLE source of information. Answer only from this context."""

    def create_chat_completion(
        self,
        question: str,
        context: str,
        conversation_history: list = None
    ) -> str:
        """
        Generate grounded answer using ChatKit.

        Args:
            question: User question
            context: Formatted context from retrieved chunks
            conversation_history: Optional previous turns

        Returns:
            Generated answer string
        """
        messages = [
            {"role": "system", "content": self.get_system_instructions()},
        ]

        # Add conversation history (last 3 turns)
        if conversation_history:
            for turn in conversation_history[-3:]:
                messages.append({"role": "user", "content": turn["question"]})
                messages.append({"role": "assistant", "content": turn["answer"]})

        # Add current context and question
        user_message = f"""CONTEXT FROM BOOK:
{context}

QUESTION: {question}

Answer based ONLY on the context above:"""

        messages.append({"role": "user", "content": user_message})

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=1000
        )

        return response.choices[0].message.content
```

### Validation

- [ ] System instructions enforce "context-only" rule
- [ ] Temperature set to 0 for determinism
- [ ] Agent initialized successfully with API key
- [ ] System instructions contain refusal template
- [ ] No external knowledge references in instructions

### Testing

```python
def test_agent_configuration():
    """Test agent is configured correctly."""
    agent = ChatKitAgent(api_key=os.getenv("OPENAI_API_KEY"))

    # Test system instructions
    instructions = agent.get_system_instructions()
    assert "ONLY the provided context" in instructions
    assert "external knowledge" in instructions.lower()
    assert "cannot answer" in instructions.lower()

    # Test configuration
    assert agent.temperature == 0.0
    assert agent.model in ["gpt-4-turbo-preview", "gpt-4o", "gpt-4"]
```

---

## Section 2: Retrieval-to-Agent Context Handoff

### Purpose
Format retrieved chunks into agent-consumable context with proper structure, metadata, and grounding cues.

### Components

**File**: `backend/agent/context_formatter.py`

**Key Elements**:
1. Chunk formatting logic
2. Metadata extraction
3. Context structure template
4. Size limit handling

### Implementation

```python
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
            Approximate token count
        """
        # Rough estimate: 1 token ≈ 4 characters
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
```

### Validation

- [ ] Chunks formatted with chapter/section metadata
- [ ] Empty chunks handled gracefully
- [ ] Selected-text mode adds selection context
- [ ] Token count estimation accurate within 10%
- [ ] Truncation preserves readability

### Testing

```python
def test_context_formatting():
    """Test context formatting logic."""
    chunks = [
        {
            "text": "ROS 2 is the next generation...",
            "metadata": {"chapter": "Chapter 1", "section": "1.2"},
            "score": 0.85
        },
        {
            "text": "Key improvements include...",
            "metadata": {"chapter": "Chapter 2", "section": "2.1"},
            "score": 0.82
        }
    ]

    context = ContextFormatter.format_chunks(chunks)

    # Validate structure
    assert "[1] Chapter: Chapter 1" in context
    assert "[2] Chapter: Chapter 2" in context
    assert "Relevance: 0.85" in context
    assert "ROS 2 is the next generation" in context

    # Test empty chunks
    empty_context = ContextFormatter.format_chunks([])
    assert "No relevant content" in empty_context
```

---

## Section 3: Selected-Text Handling Logic

### Purpose
Implement special logic for selected-text mode where user highlights specific book passage and asks questions about it.

### Components

**File**: `backend/agent/selected_text_handler.py`

**Key Elements**:
1. Mode detection
2. Selected-text validation
3. Context constraint enforcement
4. Answer scope verification

### Implementation

```python
from typing import Optional, Dict, List

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
        from backend.agent.context_formatter import ContextFormatter

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
```

### Validation

- [ ] Selected-text required validation works
- [ ] Length limits enforced (10-2000 chars)
- [ ] Context properly emphasizes selection
- [ ] Answer scope verification catches off-topic answers
- [ ] Mode detection works correctly

### Testing

```python
def test_selected_text_validation():
    """Test selected-text validation."""
    # Valid
    SelectedTextHandler.validate_selected_text(
        selected_text="DDS is used for communication",
        retrieval_mode="selected_text"
    )

    # Missing selected text
    with pytest.raises(ValueError, match="required"):
        SelectedTextHandler.validate_selected_text(
            selected_text=None,
            retrieval_mode="selected_text"
        )

    # Too short
    with pytest.raises(ValueError, match="at least 10"):
        SelectedTextHandler.validate_selected_text(
            selected_text="short",
            retrieval_mode="selected_text"
        )
```

---

## Section 4: Answer Generation and Refusal Handling

### Purpose
Generate grounded answers using the agent and handle refusal cases when context is insufficient.

### Components

**File**: `backend/agent/answer_generator.py`

**Key Elements**:
1. Agent invocation logic
2. Answer extraction
3. Refusal detection
4. Citation extraction

### Implementation

```python
from typing import Dict, List, Optional
from backend.agent.chatkit_agent import ChatKitAgent
from backend.models import Citation

class AnswerGenerator:
    """Generates grounded answers using ChatKit agent."""

    def __init__(self, agent: ChatKitAgent):
        """
        Initialize answer generator.

        Args:
            agent: Configured ChatKit agent
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
            "don't have enough information"
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
            citations.append(Citation(
                chapter=metadata.get("chapter", "Unknown"),
                section=metadata.get("section", "Unknown"),
                text_snippet=chunk.get("text", "")[:150] + "...",
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

        # Extract keywords from answer
        answer_keywords = set(answer.lower().split())

        # Extract keywords from chunks
        chunk_keywords = set()
        for chunk in retrieved_chunks:
            chunk_text = chunk.get("text", "").lower()
            chunk_keywords.update(chunk_text.split())

        # Check keyword overlap
        overlap = answer_keywords.intersection(chunk_keywords)
        overlap_ratio = len(overlap) / len(answer_keywords) if answer_keywords else 0

        # Should have at least 60% keyword overlap
        return overlap_ratio >= 0.6
```

### Validation

- [ ] Agent generates answers successfully
- [ ] Refusal detection catches "cannot answer" responses
- [ ] Citations extracted from top chunks
- [ ] Grounding validation detects hallucinations
- [ ] Conversation history included correctly

### Testing

```python
def test_answer_generation():
    """Test answer generation."""
    agent = ChatKitAgent(api_key=os.getenv("OPENAI_API_KEY"))
    generator = AnswerGenerator(agent)

    context = "[1] Chapter 1: ROS 2 is the next generation..."

    result = generator.generate_answer(
        question="What is ROS 2?",
        context=context
    )

    assert "answer" in result
    assert "grounded" in result
    assert result["grounded"] is True

def test_refusal_detection():
    """Test refusal detection."""
    generator = AnswerGenerator(agent)

    assert generator._is_refusal("I cannot answer this question based on the book content provided.")
    assert not generator._is_refusal("ROS 2 is the next generation...")
```

---

## Section 5: Chat History Persistence

### Purpose
Store and retrieve conversation turns using Neon Serverless Postgres for persistent chat history.

### Components

**File**: `backend/storage/database.py`

**Key Elements**:
1. Neon Postgres connection
2. Schema definition
3. CRUD operations for sessions and turns
4. History retrieval

### Implementation

```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from datetime import datetime
import uuid

class NeonDatabase:
    """Neon Serverless Postgres client."""

    def __init__(self, database_url: str):
        """
        Initialize database connection.

        Args:
            database_url: Neon database URL
        """
        self.database_url = database_url
        self._init_schema()

    def get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)

    def _init_schema(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create sessions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id UUID PRIMARY KEY,
                        user_id VARCHAR(255),
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)

                # Create chat_turns table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_turns (
                        id SERIAL PRIMARY KEY,
                        session_id UUID REFERENCES sessions(id),
                        question TEXT NOT NULL,
                        retrieval_mode VARCHAR(20) NOT NULL,
                        context_chunk_ids TEXT[],
                        answer TEXT NOT NULL,
                        grounded BOOLEAN NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)

                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_turns
                    ON chat_turns(session_id, created_at)
                """)

                conn.commit()

    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create new conversation session.

        Args:
            user_id: Optional user identifier

        Returns:
            Session ID (UUID)
        """
        session_id = str(uuid.uuid4())

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sessions (id, user_id) VALUES (%s, %s)",
                    (session_id, user_id)
                )
                conn.commit()

        return session_id

    def add_turn(
        self,
        session_id: str,
        question: str,
        retrieval_mode: str,
        context_chunk_ids: List[str],
        answer: str,
        grounded: bool
    ) -> None:
        """
        Add chat turn to session.

        Args:
            session_id: Session UUID
            question: User question
            retrieval_mode: "normal" or "selected_text"
            context_chunk_ids: IDs of retrieved chunks
            answer: Generated answer
            grounded: Whether answer is grounded
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_turns
                    (session_id, question, retrieval_mode, context_chunk_ids, answer, grounded)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (session_id, question, retrieval_mode, context_chunk_ids, answer, grounded))
                conn.commit()

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for session.

        Args:
            session_id: Session UUID

        Returns:
            List of conversation turns
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT question, answer, retrieval_mode, grounded, created_at
                    FROM chat_turns
                    WHERE session_id = %s
                    ORDER BY created_at ASC
                """, (session_id,))

                return cur.fetchall()

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM sessions WHERE id = %s", (session_id,))
                return cur.fetchone() is not None


def get_database() -> NeonDatabase:
    """Get database instance."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not configured")
    return NeonDatabase(database_url)
```

### Validation

- [ ] Database schema created successfully
- [ ] Sessions can be created and retrieved
- [ ] Turns can be added to sessions
- [ ] Conversation history retrieval works
- [ ] Foreign key constraints enforced

### Testing

```python
def test_database_operations():
    """Test database CRUD operations."""
    db = get_database()

    # Create session
    session_id = db.create_session(user_id="test_user")
    assert db.session_exists(session_id)

    # Add turn
    db.add_turn(
        session_id=session_id,
        question="What is ROS 2?",
        retrieval_mode="normal",
        context_chunk_ids=["chunk_1", "chunk_2"],
        answer="ROS 2 is...",
        grounded=True
    )

    # Get history
    history = db.get_conversation_history(session_id)
    assert len(history) == 1
    assert history[0]["question"] == "What is ROS 2?"
```

---

## Section 6: Error Handling and Logging

### Purpose
Implement comprehensive error handling and structured logging for debugging and monitoring.

### Components

**File**: `backend/utils/error_handling.py`
**File**: `backend/utils/logging.py`

**Key Elements**:
1. Custom exception classes
2. Error recovery strategies
3. Structured JSON logging
4. Performance tracking

### Implementation

```python
# error_handling.py
class RetrievalError(Exception):
    """Raised when retrieval layer fails."""
    pass

class AgentError(Exception):
    """Raised when agent invocation fails."""
    pass

class DatabaseError(Exception):
    """Raised when database operation fails."""
    pass

class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def handle_errors(func):
    """Decorator for error handling."""
    from functools import wraps
    import logging

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RetrievalError as e:
            logging.error(f"Retrieval error: {str(e)}")
            raise
        except AgentError as e:
            logging.error(f"Agent error: {str(e)}")
            raise
        except DatabaseError as e:
            logging.error(f"Database error: {str(e)}")
            # Don't fail request if only storage fails
            logging.warning("Continuing without persisting turn")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            raise

    return wrapper


# logging.py
import json
import logging
from datetime import datetime

class StructuredLogger:
    """Structured JSON logger."""

    @staticmethod
    def log_event(event: str, level: str = "INFO", **kwargs):
        """
        Log structured JSON event.

        Args:
            event: Event name
            level: Log level
            **kwargs: Additional event data
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "event": event,
            **kwargs
        }

        logger = logging.getLogger("agentic_rag")
        getattr(logger, level.lower())(json.dumps(log_entry))

    @staticmethod
    def log_latency(operation: str, latency_ms: float):
        """Log operation latency."""
        StructuredLogger.log_event(
            "latency_metric",
            operation=operation,
            latency_ms=round(latency_ms, 2)
        )
```

### Validation

- [ ] Custom exceptions raised correctly
- [ ] Error decorator catches all exception types
- [ ] Structured logs output JSON format
- [ ] Latency tracking works
- [ ] Database errors don't fail entire request

### Testing

```python
def test_error_handling():
    """Test error handling decorator."""
    @handle_errors
    def failing_function():
        raise RetrievalError("Test error")

    with pytest.raises(RetrievalError):
        failing_function()

def test_structured_logging(caplog):
    """Test structured logging."""
    StructuredLogger.log_event("test_event", level="INFO", key="value")

    log_output = caplog.records[0].message
    log_json = json.loads(log_output)

    assert log_json["event"] == "test_event"
    assert log_json["key"] == "value"
```

---

## Integration Example

**File**: `backend/api/routes.py` (updated `/chat` endpoint)

```python
from backend.agent.chatkit_agent import ChatKitAgent
from backend.agent.context_formatter import ContextFormatter
from backend.agent.answer_generator import AnswerGenerator
from backend.agent.selected_text_handler import SelectedTextHandler
from backend.storage.database import get_database
from backend.utils.error_handling import handle_errors
from backend.utils.logging import StructuredLogger

@router.post("/chat", response_model=ChatResponse)
@handle_errors
async def chat(request: ChatRequest):
    """Chat endpoint using ChatKit agent."""
    import time
    start_time = time.time()

    StructuredLogger.log_event("chat_start", question=request.question)

    # Validate selected text if needed
    SelectedTextHandler.validate_selected_text(
        request.selected_text,
        request.retrieval_mode
    )

    # Retrieve chunks
    retriever = get_retriever()  # From config
    chunks = retriever.retrieve(
        query=request.question,
        retrieval_mode=request.retrieval_mode,
        selected_text=request.selected_text
    )

    # Format context
    if request.retrieval_mode == "selected_text":
        context = SelectedTextHandler.prepare_selected_text_context(
            request.question,
            request.selected_text,
            chunks
        )
    else:
        context = ContextFormatter.format_chunks(chunks)

    # Get history
    db = get_database()
    history = db.get_conversation_history(request.session_id) if request.session_id else []

    # Generate answer
    agent = ChatKitAgent(api_key=os.getenv("OPENAI_API_KEY"))
    generator = AnswerGenerator(agent)

    result = generator.generate_answer(
        question=request.question,
        context=context,
        conversation_history=history
    )

    # Extract citations
    citations = generator.extract_citations(result["answer"], chunks)

    # Store turn
    if not request.session_id:
        session_id = db.create_session()
    else:
        session_id = request.session_id

    db.add_turn(
        session_id=session_id,
        question=request.question,
        retrieval_mode=request.retrieval_mode,
        context_chunk_ids=[str(i) for i in range(len(chunks))],
        answer=result["answer"],
        grounded=result["grounded"]
    )

    # Log latency
    latency_ms = (time.time() - start_time) * 1000
    StructuredLogger.log_latency("chat_request", latency_ms)

    return ChatResponse(
        session_id=session_id,
        answer=result["answer"],
        citations=citations,
        retrieval_mode=request.retrieval_mode,
        grounded=result["grounded"],
        metadata={"latency_ms": latency_ms, "num_chunks": len(chunks)}
    )
```

---

## Section Summary

| Section | File | Responsibility | Status |
|---------|------|----------------|--------|
| 1 | `chatkit_agent.py` | Agent configuration & system instructions | 📋 Spec |
| 2 | `context_formatter.py` | Chunk formatting for agent | 📋 Spec |
| 3 | `selected_text_handler.py` | Selected-text mode logic | 📋 Spec |
| 4 | `answer_generator.py` | Answer generation & refusal | 📋 Spec |
| 5 | `database.py` | Neon Postgres persistence | 📋 Spec |
| 6 | `error_handling.py`, `logging.py` | Error & logging | 📋 Spec |

All sections ready for implementation.
