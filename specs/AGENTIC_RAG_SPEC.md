# Agentic RAG Chatbot - Specification

## Overview

**Target Audience**: Hackathon judges and AI engineers evaluating agent-based reasoning grounded strictly in book content.

**Focus**: Implement an agentic RAG chatbot using OpenAI Agents SDK / ChatKit that answers user questions using only retrieved book content, supporting both full-book and selected-text question modes.

---

## Success Criteria

- [x] Agent answers grounded strictly in retrieved book chunks
- [x] Agent refuses to answer when relevant information not found in book
- [x] Agent supports both full-book and selected-text question modes
- [x] Chat history persisted and retrievable
- [x] Agent integrates cleanly with completed retrieval layer

---

## Constraints

| Constraint | Value | Notes |
|------------|-------|-------|
| Agent Framework | OpenAI Agents SDK / ChatKit | Must use this framework |
| Retrieval Layer | Pre-built semantic retrieval over Qdrant | ✅ Already implemented |
| Embeddings | Gemini free-tier | Already used in ingestion/retrieval |
| Knowledge Source | Retrieved book content only | No external knowledge |
| Reasoning Scope | Provided context only | No inference beyond context |

---

## Architecture

```
User Input (question + optional selected text)
    ↓
FastAPI Endpoint (/chat)
    ↓
Retrieval Layer (semantic search on Qdrant)
    ↓ (top-k book chunks)
Agent Runtime (OpenAI Agents SDK)
    ↓ (grounded answer)
Response + Storage (Neon Postgres)
    ↓
Return to User
```

### Component Responsibilities

1. **Retrieval Layer** (✅ Complete)
   - Semantic search via Qdrant
   - Mode detection (normal/selected-text)
   - Returns top-k chunks with metadata

2. **Agent Runtime** (New)
   - OpenAI Agents SDK / ChatKit
   - Receives retrieved context as system knowledge
   - Generates grounded answers
   - Enforces strict grounding rules

3. **Storage Layer** (New)
   - Neon Serverless Postgres
   - Persists chat turns
   - Stores context references
   - Retrievable conversation history

4. **API Orchestration** (Update existing)
   - FastAPI endpoint coordination
   - Retrieval → Agent → Storage flow
   - Error handling and logging

---

## Functional Requirements

### 1. Input Handling
- Accept user question (required)
- Accept optional selected text (for selected-text mode)
- Accept session ID (for conversation continuity)
- Validate inputs (non-empty, length limits)

### 2. Retrieval Integration
- Call existing retrieval layer
- Pass question + retrieval mode + selected text
- Receive top-k chunks with metadata
- Handle empty results gracefully

### 3. Agent Context Preparation
- Format retrieved chunks as agent context
- Include chapter/section metadata
- Structure as system-provided knowledge
- Pass to agent via ChatKit SDK

### 4. Agent Execution
- Initialize OpenAI Agents SDK agent
- Configure with strict grounding instructions
- Process question with provided context
- Generate grounded answer

### 5. Response Handling
- Extract agent answer
- Include source citations
- Return structured response
- Handle refusal cases

### 6. Persistence
- Store chat turn in Neon Postgres
- Save question, context IDs, answer
- Maintain session linkage
- Support history retrieval

---

## Agent Behavior Rules

### System Instructions

```
You are a helpful assistant that answers questions about a book.

STRICT RULES:
1. Use ONLY the provided context to answer questions
2. If the answer is not in the context, respond: "I cannot answer this question based on the book content provided."
3. Do not use external knowledge or prior information
4. Do not infer, speculate, or extrapolate beyond the context
5. Cite chapter and section when possible (format: [Chapter X, Section Y])
6. Keep answers concise and directly address the question
7. If context is ambiguous, acknowledge uncertainty

CONTEXT FORMAT:
You will receive retrieved book chunks with metadata.
Each chunk includes:
- Chapter name
- Section name
- Text content
- Relevance score

Use these chunks as your sole source of information.
```

### Grounding Enforcement

**Agent must**:
- Only reference information present in retrieved chunks
- Cite sources using chapter/section metadata
- Acknowledge when context is insufficient
- Refuse to answer if grounding is unclear

**Agent must NOT**:
- Use prior knowledge about the book's topic
- Infer information not stated in chunks
- Hallucinate facts or citations
- Answer questions outside the book's scope

---

## Non-Functional Requirements

### 1. Determinism
- Same question + same retrieved context → same answer
- Agent temperature set to 0 or low value
- No randomness in context formatting

### 2. Separation of Concerns
```
Retrieval Layer ← Already complete
    ↓
Agent Layer ← New (OpenAI Agents SDK)
    ↓
Storage Layer ← New (Neon Postgres)
```

### 3. Security
- API keys in environment variables only
- Backend-only execution
- No secrets exposed to frontend
- Secure database connection strings

### 4. Logging
- Structured logs for retrieval calls
- Agent invocation tracking
- Error logging with context
- Performance metrics (latency)

---

## NOT Building

- ❌ Frontend chat UI (backend API only)
- ❌ Re-ranking or advanced evaluation pipelines
- ❌ User authentication or personalization
- ❌ Analytics or feedback loops
- ❌ Multi-modal inputs (images, audio)
- ❌ Streaming responses (batch only for MVP)

---

## Deliverables

### 1. Agent Configuration
**File**: `backend/agent/chatkit_agent.py`

**Contents**:
- OpenAI Agents SDK / ChatKit initialization
- Agent system instructions (grounding rules)
- Context formatting logic
- Answer extraction

### 2. FastAPI Orchestration
**File**: `backend/api/routes.py` (update)

**Endpoint**: `POST /api/v1/chat`

**Flow**:
```python
1. Validate request (question, session_id, retrieval_mode, selected_text)
2. Call retrieval layer → get chunks
3. Format chunks as agent context
4. Invoke ChatKit agent with context
5. Extract grounded answer
6. Store turn in Neon Postgres
7. Return response with citations
```

### 3. Database Schema
**File**: `backend/storage/database.py`

**Tables**:
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chat_turns (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    question TEXT NOT NULL,
    retrieval_mode VARCHAR(20) NOT NULL,
    context_chunk_ids TEXT[], -- Array of chunk IDs
    answer TEXT NOT NULL,
    grounded BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_session_turns ON chat_turns(session_id, created_at);
```

### 4. Documentation
**File**: `backend/CHATKIT_AGENT_GUIDE.md`

**Contents**:
- Agent configuration details
- Grounding rules explanation
- Context formatting examples
- Testing guide
- Troubleshooting

---

## Completion Criteria

### End-to-End Flow ✅
1. User sends question → API receives
2. API calls retrieval → chunks returned
3. API formats context → ChatKit agent processes
4. Agent generates answer → stored in Neon
5. Response returned to user with citations

### Grounding Validation ✅
- Agent answers only reference retrieved chunks
- Citations match actual chapter/section metadata
- Refusal responses when context insufficient
- No hallucinated information

### Selected-Text Mode ✅
- Selected-text queries restrict retrieval
- Agent receives only constrained chunks
- Answers reflect narrowed context

### Persistence ✅
- Chat turns stored in Neon Postgres
- Session history retrievable via API
- Context references preserved

---

## Technical Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Agent Framework | OpenAI Agents SDK / ChatKit | Primary requirement |
| Backend API | FastAPI | ✅ Already implemented |
| Retrieval | Qdrant + Gemini embeddings | ✅ Already implemented |
| Database | Neon Serverless Postgres | New |
| Deployment | Railway / Render / Heroku | Optional |

---

## Environment Variables

```bash
# OpenAI Agents SDK
OPENAI_API_KEY=sk-...

# Neon Postgres
DATABASE_URL=postgresql://user:pass@neon.tech/dbname

# Existing (from retrieval layer)
QDRANT_URL=...
QDRANT_API_KEY=...
GEMINI_API_KEY=...
COLLECTION_NAME=data_collection
```

---

## Implementation Phases

### Phase 1: Neon Postgres Setup (30 min)
- Create Neon database
- Define schema (sessions, chat_turns)
- Test connection from backend
- Implement basic CRUD operations

### Phase 2: ChatKit Agent Integration (60 min)
- Install OpenAI Agents SDK / ChatKit
- Configure agent with grounding instructions
- Implement context formatting
- Test agent responses with sample context

### Phase 3: API Orchestration (45 min)
- Update `/chat` endpoint to use ChatKit agent
- Integrate retrieval → agent → storage flow
- Add error handling for agent failures
- Implement response formatting

### Phase 4: Testing & Validation (45 min)
- Test full-book questions
- Test selected-text questions
- Validate grounding (no hallucinations)
- Test conversation history
- Edge cases (no results, ambiguous context)

### Phase 5: Documentation (30 min)
- Agent configuration guide
- API usage examples
- Deployment instructions
- Troubleshooting guide

**Total**: ~3.5 hours

---

## Success Metrics

- [ ] 100% of answers grounded in retrieved content
- [ ] 0 hallucinated facts or citations
- [ ] Selected-text mode restricts context correctly
- [ ] Chat history persistence working
- [ ] API response time <3 seconds (P95)
- [ ] Clear refusal when context insufficient

---

## Example Interaction

### Full-Book Mode

**Request**:
```json
{
  "session_id": "abc-123",
  "question": "What is ROS 2?",
  "retrieval_mode": "normal"
}
```

**Retrieved Chunks**:
```
[Chapter 1, Section 1.2] ROS 2 is the next generation of the Robot Operating System...
[Chapter 2, Section 2.1] Key improvements in ROS 2 include real-time capabilities...
```

**Agent Response**:
```json
{
  "answer": "ROS 2 is the next generation of the Robot Operating System with key improvements including real-time capabilities. [Chapter 1, Section 1.2; Chapter 2, Section 2.1]",
  "grounded": true,
  "citations": [
    {"chapter": "Chapter 1", "section": "Section 1.2"},
    {"chapter": "Chapter 2", "section": "Section 2.1"}
  ]
}
```

### Selected-Text Mode

**Request**:
```json
{
  "question": "Explain this concept",
  "retrieval_mode": "selected_text",
  "selected_text": "DDS is used for inter-node communication"
}
```

**Retrieved Chunks**:
```
[Chapter 3, Section 3.4] DDS (Data Distribution Service) is the middleware used for inter-node communication in ROS 2...
```

**Agent Response**:
```json
{
  "answer": "DDS (Data Distribution Service) is the middleware used for inter-node communication in ROS 2. [Chapter 3, Section 3.4]",
  "grounded": true,
  "citations": [
    {"chapter": "Chapter 3", "section": "Section 3.4"}
  ]
}
```

### Insufficient Context

**Request**:
```json
{
  "question": "What is quantum computing?",
  "retrieval_mode": "normal"
}
```

**Retrieved Chunks**: (empty or irrelevant)

**Agent Response**:
```json
{
  "answer": "I cannot answer this question based on the book content provided.",
  "grounded": true,
  "citations": []
}
```

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent hallucination | High | Strict system instructions, grounding validation |
| Neon Postgres downtime | Medium | Connection retry logic, error handling |
| ChatKit SDK changes | Low | Pin SDK version in requirements.txt |
| Empty retrieval results | Medium | Clear refusal messages, logging |
| Slow agent responses | Medium | Timeout configuration, latency monitoring |

---

## Comparison to Current Implementation

### Current (Claude 3.5 Sonnet via OpenRouter)
- ✅ Custom orchestration
- ✅ Manual grounding validation
- ✅ In-memory session storage
- ❌ No agent framework

### New (OpenAI Agents SDK / ChatKit)
- ✅ Framework-based agent runtime
- ✅ Built-in conversation management
- ✅ Persistent storage (Neon Postgres)
- ✅ Standard SDK patterns
- ✅ Better scalability

### Migration Path
1. Keep existing retrieval layer (no changes)
2. Replace custom agent with ChatKit
3. Replace in-memory storage with Neon Postgres
4. Update API orchestration
5. Maintain backward-compatible endpoints

---

## Next Steps

1. **Setup Neon Postgres**: Create database, define schema
2. **Install ChatKit SDK**: Add to requirements.txt
3. **Configure Agent**: System instructions, grounding rules
4. **Update API**: Integrate ChatKit agent
5. **Test**: Full flow validation
6. **Document**: Usage guide and examples

---

**Status**: 📋 Specification complete, ready for implementation

**Estimated Duration**: 3.5 hours

**Dependencies**: Retrieval layer ✅, Neon Postgres account, OpenAI API key
