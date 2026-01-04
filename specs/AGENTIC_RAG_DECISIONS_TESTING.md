# Agentic RAG - Decisions and Testing Strategy

## Architectural Decisions

### Decision 1: OpenAI Agents SDK / ChatKit for Agent Orchestration

**Options Considered**:

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **OpenAI Agents SDK** | Standard framework, built-in conversation management, community support | Requires OpenAI API key, costs per token | ✅ **SELECTED** |
| Claude via OpenRouter | Already integrated (Step 2), familiar | Not an agent framework, manual orchestration | ❌ Rejected |
| LangChain | Full-featured, many integrations | Heavy dependency, complex for simple use case | ❌ Rejected |
| Custom Framework | Full control, no external dependencies | Reinventing the wheel, maintenance burden | ❌ Rejected |

**Decision**: OpenAI Agents SDK / ChatKit

**Rationale**:
- **Requirement**: Specification explicitly requires OpenAI Agents SDK / ChatKit
- **Simplicity**: Clean API, minimal boilerplate
- **Reliability**: Production-tested framework
- **Conversation Management**: Built-in history handling
- **Grounding Support**: System instructions for strict context adherence

**Implementation**:
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": "Use only provided context..."},
        {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
    ],
    temperature=0.0
)
```

---

### Decision 2: Separation of Concerns (Retrieval vs Agent Reasoning)

**Architecture**:

```
┌─────────────────┐         ┌─────────────────┐
│ Retrieval Layer │────────▶│   Agent Layer   │
│  (retrieval/)   │ chunks  │  (chatkit_agent)│
└─────────────────┘         └─────────────────┘
        │                            │
        │                            │
    Concerns:                    Concerns:
    • Semantic search            • Reasoning
    • Embeddings                 • Grounding
    • Top-k selection            • Citations
    • Mode detection             • Refusals
```

**Why Separate**:
1. **Single Responsibility**: Each layer has one job
2. **Testability**: Can test retrieval without agent, agent without retrieval
3. **Reusability**: Retrieval layer used by multiple components
4. **Debugging**: Easier to isolate issues
5. **Performance**: Can optimize each layer independently

**Interface Contract**:
```python
# Retrieval layer provides:
chunks: List[Dict] = retriever.retrieve(query, mode, selected_text)

# Agent layer expects:
def generate_answer(question: str, context: str) -> str
```

**Trade-offs**:
- ✅ Pro: Clean separation, easier to maintain
- ✅ Pro: Can swap retrieval or agent independently
- ❌ Con: Extra layer of abstraction
- ❌ Con: Need to format chunks → context

**Decision**: Maintain strict separation

---

### Decision 3: Context Window Strategy

**Challenge**: Balance between providing enough context and staying within token limits.

**Options**:

| Strategy | Context Size | Pros | Cons | Verdict |
|----------|--------------|------|------|---------|
| **Top-k chunks** | Variable (k=5) | Simple, predictable | May miss relevant info | ✅ **SELECTED** |
| Dynamic token budget | Up to max tokens | Uses full capacity | Complex, unpredictable | ❌ Rejected |
| All matching chunks | All above threshold | Comprehensive | Can exceed limits | ❌ Rejected |
| Summarize chunks | Fixed summary size | Consistent size | Loses detail | ❌ Rejected |

**Decision**: Top-k chunks with truncation fallback

**Parameters**:
- **Normal mode**: k=5, max 2000 tokens
- **Selected-text mode**: k=3, max 1200 tokens
- **Truncation threshold**: 4000 tokens (safety margin)

**Implementation**:
```python
def prepare_context(chunks: List[Dict], mode: str) -> str:
    k = 3 if mode == "selected_text" else 5
    selected_chunks = chunks[:k]

    context = ContextFormatter.format_chunks(selected_chunks)

    # Truncate if needed
    if ContextFormatter.get_token_count(context) > 4000:
        context = ContextFormatter.truncate(context, max_tokens=4000)

    return context
```

**Rationale**:
- Simplicity over optimization
- Predictable behavior
- Well within GPT-4 Turbo limits (128k tokens)
- Easy to debug and test

---

### Decision 4: Refusal Strategy When Answer Not Found

**Options**:

| Strategy | Example Response | User Experience | Verdict |
|----------|------------------|-----------------|---------|
| **Explicit refusal** | "I cannot answer this question based on the book content provided." | Clear, honest | ✅ **SELECTED** |
| Best-effort answer | "Based on limited context..." + disclaimer | Helpful but risky | ❌ Rejected |
| Empty response | "" | Confusing | ❌ Rejected |
| Suggest rephrasing | "Try rephrasing: ..." | Helpful but complex | ❌ Rejected |

**Decision**: Explicit refusal with standard message

**Standard Refusal Template**:
```
"I cannot answer this question based on the book content provided."
```

**When to Refuse**:
1. No relevant chunks retrieved (empty result)
2. Retrieved chunks have low relevance scores (all below 0.5)
3. Agent cannot find answer in provided context
4. Question is ambiguous or unclear

**Agent Instructions**:
```
If the answer is not in the context, respond EXACTLY:
"I cannot answer this question based on the book content provided."

Do not attempt to answer from external knowledge.
```

**Rationale**:
- **Honesty**: Better to refuse than hallucinate
- **Trust**: Users know system is reliable
- **Clarity**: Unambiguous message
- **Simplicity**: Easy to detect in code

**Detection Logic**:
```python
def is_refusal(answer: str) -> bool:
    refusal_phrases = [
        "cannot answer",
        "not in the context",
        "not found in the book"
    ]
    return any(phrase in answer.lower() for phrase in refusal_phrases)
```

---

### Decision 5: Chat History Storage (Neon Serverless Postgres)

**Options**:

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Neon Postgres** | Persistent, SQL, free tier, serverless | Requires connection management | ✅ **SELECTED** |
| In-memory (current) | Fast, simple | Not persistent, lost on restart | ❌ Rejected |
| Redis | Fast, persistent | Extra service, cost | ❌ Rejected |
| SQLite | Simple, local | Not serverless, scaling issues | ❌ Rejected |
| MongoDB | Flexible schema | NoSQL, extra service | ❌ Rejected |

**Decision**: Neon Serverless Postgres

**Schema Design**:
```sql
-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat turns table
CREATE TABLE chat_turns (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    question TEXT NOT NULL,
    retrieval_mode VARCHAR(20) NOT NULL,
    context_chunk_ids TEXT[],  -- Array of chunk IDs
    answer TEXT NOT NULL,
    grounded BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast history retrieval
CREATE INDEX idx_session_turns ON chat_turns(session_id, created_at);
```

**Rationale**:
- **Free Tier**: 0.5 GB storage, 100 hours compute (sufficient for MVP)
- **Serverless**: Auto-scaling, auto-suspend
- **SQL**: Familiar query language
- **Managed**: No database administration
- **Persistent**: Survives restarts
- **Queryable**: Can analyze conversations

**Connection Strategy**:
```python
import psycopg2
from psycopg2.pool import SimpleConnectionPool

# Connection pool for efficiency
pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=os.getenv("DATABASE_URL")
)
```

---

## Testing Strategy

### Phase 1: Unit Testing (During Implementation)

**Test Coverage Goals**: >90%

**1.1 Agent Configuration**
```python
def test_agent_initialization():
    """Test agent initializes correctly."""
    agent = ChatKitAgent(api_key="test_key")
    assert agent.temperature == 0.0
    assert agent.model in ["gpt-4-turbo-preview", "gpt-4o"]

def test_system_instructions():
    """Test system instructions enforce grounding."""
    agent = ChatKitAgent(api_key="test_key")
    instructions = agent.get_system_instructions()

    assert "ONLY the provided context" in instructions
    assert "cannot answer" in instructions.lower()
    assert "external knowledge" in instructions.lower()
```

**1.2 Context Formatting**
```python
def test_chunk_formatting():
    """Test chunks formatted correctly."""
    chunks = [
        {"text": "ROS 2 is...", "metadata": {"chapter": "Ch1", "section": "1.2"}, "score": 0.85}
    ]

    context = ContextFormatter.format_chunks(chunks)

    assert "[1] Chapter: Ch1" in context
    assert "Section: 1.2" in context
    assert "ROS 2 is..." in context

def test_empty_chunks():
    """Test empty chunks handled."""
    context = ContextFormatter.format_chunks([])
    assert "No relevant content" in context
```

**1.3 Selected-Text Validation**
```python
def test_selected_text_validation():
    """Test selected text validation."""
    # Valid
    SelectedTextHandler.validate_selected_text(
        "DDS is used for communication",
        "selected_text"
    )

    # Missing
    with pytest.raises(ValueError):
        SelectedTextHandler.validate_selected_text(None, "selected_text")

    # Too short
    with pytest.raises(ValueError):
        SelectedTextHandler.validate_selected_text("short", "selected_text")
```

**1.4 Database Operations**
```python
def test_create_session():
    """Test session creation."""
    db = get_database()
    session_id = db.create_session(user_id="test_user")

    assert db.session_exists(session_id)

def test_add_turn():
    """Test adding chat turn."""
    db = get_database()
    session_id = db.create_session()

    db.add_turn(
        session_id=session_id,
        question="What is ROS 2?",
        retrieval_mode="normal",
        context_chunk_ids=["chunk_1"],
        answer="ROS 2 is...",
        grounded=True
    )

    history = db.get_conversation_history(session_id)
    assert len(history) == 1
    assert history[0]["question"] == "What is ROS 2?"
```

---

### Phase 2: Integration Testing (After Core Implementation)

**2.1 End-to-End Flow**
```python
def test_full_chat_flow():
    """Test complete chat flow."""
    # Setup
    retriever = get_retriever()
    agent = ChatKitAgent(api_key=os.getenv("OPENAI_API_KEY"))
    db = get_database()

    # Retrieve
    chunks = retriever.retrieve(query="What is ROS 2?", retrieval_mode="normal")
    assert len(chunks) > 0

    # Format context
    context = ContextFormatter.format_chunks(chunks)
    assert "Chapter" in context

    # Generate answer
    generator = AnswerGenerator(agent)
    result = generator.generate_answer(
        question="What is ROS 2?",
        context=context
    )

    assert "answer" in result
    assert result["grounded"] is True

    # Store turn
    session_id = db.create_session()
    db.add_turn(
        session_id=session_id,
        question="What is ROS 2?",
        retrieval_mode="normal",
        context_chunk_ids=["chunk_1"],
        answer=result["answer"],
        grounded=result["grounded"]
    )

    # Verify storage
    history = db.get_conversation_history(session_id)
    assert len(history) == 1
```

**2.2 Determinism Test**
```python
def test_deterministic_responses():
    """Test same input produces same output."""
    agent = ChatKitAgent(api_key=os.getenv("OPENAI_API_KEY"))
    generator = AnswerGenerator(agent)

    context = "[1] Chapter 1: ROS 2 is the next generation..."

    result1 = generator.generate_answer("What is ROS 2?", context)
    result2 = generator.generate_answer("What is ROS 2?", context)
    result3 = generator.generate_answer("What is ROS 2?", context)

    # Should be identical (temperature=0)
    assert result1["answer"] == result2["answer"] == result3["answer"]
```

---

### Phase 3: Grounding Validation Tests

**3.1 Grounded Answer Test**
```python
def test_grounded_answer():
    """Test agent produces grounded answer."""
    agent = ChatKitAgent(api_key=os.getenv("OPENAI_API_KEY"))
    generator = AnswerGenerator(agent)

    chunks = [
        {
            "text": "ROS 2 is the next generation of the Robot Operating System.",
            "metadata": {"chapter": "Chapter 1", "section": "1.2"},
            "score": 0.85
        }
    ]

    context = ContextFormatter.format_chunks(chunks)

    result = generator.generate_answer(
        question="What is ROS 2?",
        context=context
    )

    # Answer should reference ROS 2
    assert "ROS 2" in result["answer"]

    # Answer should be grounded
    assert generator.validate_grounding(result["answer"], chunks)

    # Answer should cite chapter
    assert "Chapter 1" in result["answer"] or "[1]" in result["answer"]
```

**3.2 Refusal Test (Out-of-Scope Question)**
```python
def test_refusal_out_of_scope():
    """Test agent refuses out-of-scope questions."""
    agent = ChatKitAgent(api_key=os.getenv("OPENAI_API_KEY"))
    generator = AnswerGenerator(agent)

    # Context about ROS 2
    chunks = [
        {
            "text": "ROS 2 uses DDS for communication.",
            "metadata": {"chapter": "Chapter 3", "section": "3.4"},
            "score": 0.60
        }
    ]

    context = ContextFormatter.format_chunks(chunks)

    # Ask unrelated question
    result = generator.generate_answer(
        question="What is quantum computing?",
        context=context
    )

    # Should refuse
    assert generator._is_refusal(result["answer"])
    assert "cannot answer" in result["answer"].lower()
```

**3.3 Hallucination Detection Test**
```python
def test_no_hallucination():
    """Test agent doesn't hallucinate facts."""
    agent = ChatKitAgent(api_key=os.getenv("OPENAI_API_KEY"))
    generator = AnswerGenerator(agent)

    chunks = [
        {
            "text": "ROS 2 supports real-time capabilities.",
            "metadata": {"chapter": "Chapter 2", "section": "2.1"},
            "score": 0.80
        }
    ]

    context = ContextFormatter.format_chunks(chunks)

    result = generator.generate_answer(
        question="What are the features of ROS 2?",
        context=context
    )

    # Answer should not mention features not in context
    forbidden_keywords = ["python", "gazebo", "docker"]  # Not in context

    for keyword in forbidden_keywords:
        assert keyword.lower() not in result["answer"].lower()
```

---

### Phase 4: Selected-Text Mode Validation

**4.1 Selected-Text Context Restriction**
```python
def test_selected_text_restricts_context():
    """Test selected text mode restricts retrieval."""
    retriever = get_retriever()

    # Normal mode
    normal_chunks = retriever.retrieve(
        query="Explain ROS 2",
        retrieval_mode="normal"
    )

    # Selected-text mode
    selected_chunks = retriever.retrieve(
        query="Explain this",
        retrieval_mode="selected_text",
        selected_text="DDS is used for communication"
    )

    # Selected-text should return fewer chunks
    assert len(selected_chunks) <= len(normal_chunks)

    # Selected-text chunks should have higher scores
    if selected_chunks:
        assert selected_chunks[0]["score"] >= 0.85
```

**4.2 Answer Scope Verification**
```python
def test_selected_text_answer_scope():
    """Test answer focuses on selected text."""
    agent = ChatKitAgent(api_key=os.getenv("OPENAI_API_KEY"))
    generator = AnswerGenerator(agent)

    selected_text = "DDS is the middleware for communication"

    chunks = [
        {
            "text": "DDS (Data Distribution Service) is the middleware used for inter-node communication in ROS 2.",
            "metadata": {"chapter": "Chapter 3", "section": "3.4"},
            "score": 0.88
        }
    ]

    context = ContextFormatter.format_selected_text_context(selected_text, chunks)

    result = generator.generate_answer(
        question="What does this mean?",
        context=context
    )

    # Answer should reference DDS
    assert "DDS" in result["answer"]

    # Verify scope
    assert SelectedTextHandler.verify_answer_scope(
        result["answer"],
        selected_text
    )
```

---

### Phase 5: Performance and Edge Cases

**5.1 Latency Test**
```python
def test_response_latency():
    """Test response completes within acceptable time."""
    import time

    agent = ChatKitAgent(api_key=os.getenv("OPENAI_API_KEY"))
    generator = AnswerGenerator(agent)

    context = ContextFormatter.format_chunks([
        {"text": "ROS 2 is...", "metadata": {"chapter": "Ch1", "section": "1.2"}, "score": 0.85}
    ])

    start = time.time()
    result = generator.generate_answer("What is ROS 2?", context)
    elapsed = time.time() - start

    # Should complete within 5 seconds
    assert elapsed < 5.0
```

**5.2 Empty Retrieval Results**
```python
def test_empty_retrieval_results():
    """Test handling of empty retrieval results."""
    agent = ChatKitAgent(api_key=os.getenv("OPENAI_API_KEY"))
    generator = AnswerGenerator(agent)

    context = ContextFormatter.format_chunks([])  # Empty

    result = generator.generate_answer(
        question="What is ROS 2?",
        context=context
    )

    # Should refuse
    assert generator._is_refusal(result["answer"])
```

**5.3 Conversation History Continuity**
```python
def test_conversation_continuity():
    """Test multi-turn conversation."""
    db = get_database()
    agent = ChatKitAgent(api_key=os.getenv("OPENAI_API_KEY"))
    generator = AnswerGenerator(agent)

    session_id = db.create_session()

    # Turn 1
    context1 = "[1] Chapter 1: ROS 2 is the next generation..."
    result1 = generator.generate_answer("What is ROS 2?", context1)

    db.add_turn(
        session_id=session_id,
        question="What is ROS 2?",
        retrieval_mode="normal",
        context_chunk_ids=["chunk_1"],
        answer=result1["answer"],
        grounded=True
    )

    # Turn 2 (follow-up)
    history = db.get_conversation_history(session_id)

    context2 = "[1] Chapter 2: ROS 2 has real-time capabilities..."
    result2 = generator.generate_answer(
        question="Tell me more about that",
        context=context2,
        conversation_history=history
    )

    # Should reference previous context
    assert "ROS 2" in result2["answer"]
```

---

## Testing Checklist

### Grounding Validation ✅
- [ ] Agent answers only reference retrieved chunks
- [ ] No external knowledge used
- [ ] Citations match actual chapter/section metadata
- [ ] Refusal responses when context insufficient
- [ ] No hallucinated facts or citations

### Selected-Text Mode ✅
- [ ] Selected-text queries restrict retrieval correctly
- [ ] Agent receives only constrained chunks
- [ ] Answers reflect narrowed context
- [ ] Keyword overlap validation passes
- [ ] Mode switching works correctly

### Chat History ✅
- [ ] Sessions created successfully
- [ ] Turns stored in Neon Postgres
- [ ] History retrievable via API
- [ ] Context references preserved
- [ ] Timestamps accurate

### Determinism ✅
- [ ] Same question → same answer (with same context)
- [ ] Temperature=0 enforced
- [ ] No randomness in context formatting
- [ ] Repeat queries produce identical results

### Performance ✅
- [ ] API response time <3 seconds (P95)
- [ ] Retrieval latency <500ms
- [ ] Agent processing <2.5 seconds
- [ ] Database operations <200ms
- [ ] No memory leaks

### Edge Cases ✅
- [ ] Empty retrieval results handled
- [ ] Malformed inputs rejected
- [ ] Database connection failures handled
- [ ] API rate limits respected
- [ ] Long questions truncated appropriately

---

## Research-Concurrent Approach

**Principle**: Test agent behavior while integrating retrieval, don't wait until the end.

**Workflow**:
```
Day 1: Setup + Initial Tests
    ├─ Morning: Neon Postgres setup
    │  └─ Test: Session CRUD operations
    ├─ Afternoon: ChatKit agent configuration
    │  └─ Test: Agent initialization, system instructions
    └─ Evening: Context formatting
       └─ Test: Chunk formatting, truncation

Day 2: Integration + Validation
    ├─ Morning: Retrieval-to-agent handoff
    │  └─ Test: End-to-end flow with mock retrieval
    ├─ Afternoon: Selected-text handling
    │  └─ Test: Mode switching, context restriction
    └─ Evening: Real retrieval integration
       └─ Test: Grounding validation, refusal behavior

Day 3: Polish + Documentation
    ├─ Morning: Error handling + logging
    │  └─ Test: Exception handling, structured logs
    ├─ Afternoon: Performance optimization
    │  └─ Test: Latency benchmarks, load testing
    └─ Evening: Documentation + examples
       └─ Test: Example requests, troubleshooting guide
```

**Benefits**:
- Catch issues early
- Validate assumptions incrementally
- Iterate on design based on test results
- Confidence in grounding before full integration

---

**Status**: All decisions documented, testing strategy defined, ready for implementation.
