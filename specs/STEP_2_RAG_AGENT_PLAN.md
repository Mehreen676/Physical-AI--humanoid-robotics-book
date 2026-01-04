# Step 2: RAG Agent Implementation - Comprehensive Plan

## Executive Summary

**Goal**: Build a production-ready, hallucination-free RAG chatbot that answers questions about book content using retrieval-augmented generation with Claude 3.5 Sonnet.

**Status**: 📋 PLANNING PHASE

**Implementation Date**: 2026-01-03

**Location**: `backend/` directory

**Target Audience**: Hackathon judges, AI engineers, production users

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG AGENT ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│              │         │              │         │              │
│   FastAPI    │────────▶│  Book RAG    │────────▶│   Qdrant     │
│   REST API   │         │    Agent     │         │  Vector DB   │
│              │         │              │         │              │
│  • /chat     │         │  Orchestrate │         │  • Search    │
│  • /sessions │         │  Sub-agents  │         │  • Filter    │
│  • /health   │         │              │         │  • Score     │
│              │         │              │         │              │
└──────────────┘         └──────────────┘         └──────────────┘
                                 │
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌──────────────┐         ┌──────────────┐       ┌──────────────┐
│              │         │              │       │              │
│  Retrieval   │         │   Answer     │       │  Guardrails  │
│  Sub-Agent   │         │  Sub-Agent   │       │  Sub-Agent   │
│              │         │              │       │              │
│  • Query     │         │  • Compose   │       │  • Validate  │
│  • Embed     │         │  • Ground    │       │  • Detect    │
│  • Filter    │         │  • Cite      │       │  • Reject    │
│              │         │              │       │              │
└──────────────┘         └──────────────┘       └──────────────┘
         │                       │                       │
         │                       ▼                       │
         │               ┌──────────────┐               │
         └──────────────▶│   Claude     │◀──────────────┘
                         │  3.5 Sonnet  │
                         │              │
                         │  • Generate  │
                         │  • Reasoning │
                         │  • Refine    │
                         │              │
                         └──────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       SUPPORTING SERVICES                        │
├─────────────────────────────────────────────────────────────────┤
│  • PostgreSQL (Session Storage)                                  │
│  • Gemini Embeddings (Query Vectorization)                       │
│  • OpenRouter (Claude 3.5 Sonnet Access)                         │
│  • Logging (Structured JSON logs)                                │
│  • Error Handling (Custom exceptions + retry logic)              │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Interaction Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        REQUEST FLOW                              │
└─────────────────────────────────────────────────────────────────┘

User Question
      │
      ▼
┌──────────────────┐
│ FastAPI Endpoint │  POST /chat
│  (routes.py)     │  { session_id, question, retrieval_mode }
└──────────────────┘
      │
      ▼
┌──────────────────┐
│   BookRAGAgent   │  Main orchestrator
│   (agent.py)     │  - Loads session history
└──────────────────┘  - Coordinates sub-agents
      │               - Returns grounded answer
      │
      ├─────────────────────────────────────────────────────┐
      │                                                     │
      ▼                                                     ▼
┌──────────────────┐                              ┌──────────────────┐
│ RetrievalSubAgent│  Step 1: Retrieve context    │  MemorySubAgent  │
│  (sub_agents.py) │                               │  (sub_agents.py) │
└──────────────────┘                              └──────────────────┘
│                                                           │
│ • Detect selected text mode                              │
│ • Embed query (Gemini)                                   │
│ • Search Qdrant (top-k=5)                                │
│ • Filter by score threshold (0.7)                        │
│ • Format chunks with metadata                            │
│                                                           │ • Load conversation
│                                                           │   history (last 10)
│                                                           │ • Format messages
│                                                           │ • Provide context
      │                                                     │
      └─────────────────────────┬───────────────────────────┘
                                │
                                ▼
                      ┌──────────────────┐
                      │  AnswerSubAgent  │  Step 2: Generate answer
                      │  (sub_agents.py) │
                      └──────────────────┘
                                │
                                │ • Construct RAG prompt
                                │ • Include retrieved chunks
                                │ • Include conversation history
                                │ • Call Claude 3.5 Sonnet
                                │ • Extract answer + citations
                                │
                                ▼
                      ┌──────────────────┐
                      │ GuardrailsSubAgent│ Step 3: Validate
                      │  (sub_agents.py) │
                      └──────────────────┘
                                │
                                │ • Check grounding
                                │ • Detect hallucinations
                                │ • Validate citations
                                │ • Reject if unsafe
                                │
                                ▼
                      ┌──────────────────┐
                      │  Save to Session │  Step 4: Persist
                      │  (storage/...)   │
                      └──────────────────┘
                                │
                                ▼
                         Return to User
                   { answer, citations, sources }
```

---

## Section Structure

### Phase 1: Project Setup & Configuration ⏸️

**Duration**: 30 minutes

**Goal**: Initialize backend directory structure, install dependencies, configure environment

**Tasks**:
- [ ] Create `backend/` directory structure
  - `backend/main.py` - FastAPI app entry point
  - `backend/config.py` - Environment configuration
  - `backend/requirements.txt` - Python dependencies
- [ ] Create module directories
  - `backend/agent/` - RAG agent and sub-agents
  - `backend/rag/` - Retrieval and grounding skills
  - `backend/api/` - API routes and middleware
  - `backend/services/` - External service integrations
  - `backend/storage/` - Database models and sessions
  - `backend/models/` - Pydantic schemas
  - `backend/utils/` - Utilities and error handling
- [ ] Install dependencies
  - FastAPI (web framework)
  - Uvicorn (ASGI server)
  - SQLAlchemy (PostgreSQL ORM)
  - Psycopg2-binary (PostgreSQL driver)
  - qdrant-client (vector database)
  - google-generativeai (Gemini embeddings)
  - httpx (HTTP client for OpenRouter)
  - pydantic (data validation)
  - python-dotenv (environment variables)
  - pytest (testing framework)
- [ ] Configure environment variables in `backend/.env`
  - `DATABASE_URL` - PostgreSQL connection string
  - `QDRANT_URL` - Qdrant Cloud endpoint
  - `QDRANT_API_KEY` - Qdrant authentication
  - `COLLECTION_NAME` - Vector collection name
  - `GEMINI_API_KEY` - Gemini embeddings API
  - `OPENROUTER_API_KEY` - Claude 3.5 Sonnet access
  - `MODEL_NAME` - LLM model identifier
  - `PORT` - Server port (8000 local, 10000 production)
- [ ] Create `.env.example` template

**Output**: Configured backend directory with all dependencies installed

**Dependencies**: None (fresh start)

---

### Phase 2: Database & Session Management ⏸️

**Duration**: 45 minutes

**Goal**: Set up PostgreSQL schema, session storage, conversation history persistence

**Tasks**:
- [ ] Create `storage/models.py` - SQLAlchemy models
  - `Session` table (id, created_at, updated_at)
  - `Message` table (id, session_id, role, content, timestamp)
  - Relationships: Session.messages (one-to-many)
- [ ] Create `storage/init_db.py` - Database initialization
  - Create tables with `create_all()`
  - Connection pooling configuration
  - Migration strategy (Alembic optional for v2)
- [ ] Create `storage/sessions.py` - Session management service
  - `create_session()` - Generate UUID, persist to DB
  - `get_session(session_id)` - Load session + messages
  - `save_message(session_id, role, content)` - Append message
  - `list_sessions()` - Get all sessions (optional)
  - `delete_session(session_id)` - Cleanup (optional)
- [ ] Test database connectivity
  - Unit test: Create session → retrieve → verify
  - Test message persistence
  - Test conversation history loading

**Output**: Working PostgreSQL schema with session CRUD operations

**Dependencies**: Phase 1 (config loaded)

**Schema Design**:

```sql
-- sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- messages table
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- indexes
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
```

---

### Phase 3: External Services Integration ⏸️

**Duration**: 60 minutes

**Goal**: Integrate Gemini embeddings, Qdrant vector search, OpenRouter LLM

**Tasks**:

#### 3.1 Gemini Embeddings Service
- [ ] Create `services/embeddings.py`
  - `GeminiEmbeddings` class (reuse from ingestion/)
  - `embed_query(text)` - Generate 768-dim query embedding
  - Error handling (quota limits, network failures)
  - Rate limiting (15 req/min)
  - Caching (optional for repeated queries)

#### 3.2 Qdrant Vector Search
- [ ] Create `rag/retrieval.py`
  - `QdrantRetriever` class
  - `search(query_vector, top_k, score_threshold, filters)`
  - `filter_by_chapter(chapter_name)` - Metadata filtering
  - `format_results(search_results)` - Convert to chunks
  - Connection pooling for concurrent requests

#### 3.3 OpenRouter LLM Service
- [ ] Create `services/openrouter_service.py`
  - `OpenRouterClient` class
  - `generate(prompt, max_tokens, temperature)`
  - Claude 3.5 Sonnet specific configuration
  - Retry logic (exponential backoff)
  - Token usage tracking
  - Error handling (rate limits, model unavailability)

**Output**: Three working service integrations with error handling

**Dependencies**: Phase 1 (environment variables), Ingestion Step 1 (embeddings code)

**API Specifications**:

```python
# Gemini Embeddings
class GeminiEmbeddings:
    def embed_query(self, text: str) -> List[float]:
        """Generate 768-dim embedding for query text."""
        # Implementation from ingestion/embeddings.py
        pass

# Qdrant Retriever
class QdrantRetriever:
    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.7,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search Qdrant and return relevant chunks."""
        pass

# OpenRouter Client
class OpenRouterClient:
    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1500,
        temperature: float = 0.0
    ) -> str:
        """Call Claude 3.5 Sonnet via OpenRouter."""
        pass
```

---

### Phase 4: RAG Sub-Agents Implementation ⏸️

**Duration**: 90 minutes

**Goal**: Build specialized sub-agents for retrieval, answer generation, guardrails, memory

**Tasks**:

#### 4.1 Retrieval Sub-Agent
- [ ] Create `agent/sub_agents.py:RetrievalSubAgent`
  - Detect retrieval mode (normal vs selected text)
  - Embed query using Gemini
  - Search Qdrant with score threshold
  - Return formatted chunks with metadata
  - Handle "no results found" gracefully

#### 4.2 Answer Sub-Agent
- [ ] Create `agent/sub_agents.py:AnswerSubAgent`
  - Construct RAG prompt template
  - Include retrieved chunks in prompt
  - Include conversation history (last 10 messages)
  - Call Claude 3.5 Sonnet via OpenRouter
  - Parse response (answer + citations)
  - Format citations with chapter/section/URL

#### 4.3 Guardrails Sub-Agent
- [ ] Create `agent/sub_agents.py:GuardrailsSubAgent`
  - Check if answer is grounded in retrieved chunks
  - Detect hallucination patterns (e.g., "I don't know" → good)
  - Validate citation accuracy (sources exist in chunks)
  - Reject answers with low confidence
  - Return validation result + reason

#### 4.4 Memory Sub-Agent
- [ ] Create `agent/sub_agents.py:MemorySubAgent`
  - Load conversation history from database
  - Format for LLM context window
  - Limit to last 10 messages (prevent context overflow)
  - Summarize older messages (optional v2 feature)

**Output**: Four working sub-agents with clear interfaces

**Dependencies**: Phase 2 (session storage), Phase 3 (services)

**Sub-Agent Interfaces**:

```python
class RetrievalSubAgent:
    async def retrieve(
        self,
        question: str,
        retrieval_mode: str,
        selected_text: Optional[str] = None
    ) -> List[Dict]:
        """Retrieve relevant chunks from Qdrant."""
        pass

class AnswerSubAgent:
    async def generate_answer(
        self,
        question: str,
        retrieved_chunks: List[Dict],
        conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """Generate grounded answer with citations."""
        pass

class GuardrailsSubAgent:
    async def validate(
        self,
        answer: str,
        retrieved_chunks: List[Dict],
        citations: List[Dict]
    ) -> Dict[str, Any]:
        """Validate answer for hallucinations."""
        pass

class MemorySubAgent:
    async def load_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Load conversation history."""
        pass
```

---

### Phase 5: Main RAG Agent Orchestration ⏸️

**Duration**: 45 minutes

**Goal**: Build main orchestrator that coordinates all sub-agents

**Tasks**:
- [ ] Create `agent/agent.py:BookRAGAgent`
  - Initialize with config and services
  - Orchestrate sub-agent workflow:
    1. Load conversation history (MemorySubAgent)
    2. Retrieve relevant chunks (RetrievalSubAgent)
    3. Generate answer (AnswerSubAgent)
    4. Validate answer (GuardrailsSubAgent)
    5. Save message to session (storage)
  - Handle errors at each step
  - Return final response or error message
- [ ] Implement agent state management
  - Track current step for debugging
  - Log agent decisions
  - Measure step latencies
- [ ] Add graceful degradation
  - If retrieval fails → use conversation history only
  - If guardrails fail → warn but don't block
  - If LLM fails → return helpful error message

**Output**: Main orchestrator agent that coordinates full RAG pipeline

**Dependencies**: Phase 2 (storage), Phase 3 (services), Phase 4 (sub-agents)

**Agent Interface**:

```python
class BookRAGAgent:
    async def chat(
        self,
        session_id: str,
        question: str,
        retrieval_mode: str = "normal",
        selected_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main chat method that orchestrates RAG pipeline.

        Returns:
            {
                "answer": str,
                "citations": List[Dict],
                "sources": List[str],
                "metadata": {
                    "chunks_retrieved": int,
                    "model_used": str,
                    "latency_ms": int
                }
            }
        """
        pass
```

---

### Phase 6: FastAPI REST API ⏸️

**Duration**: 60 minutes

**Goal**: Build REST API endpoints for chat, sessions, health checks

**Tasks**:

#### 6.1 API Routes
- [ ] Create `api/routes.py`
  - `POST /chat` - Main chat endpoint
  - `POST /sessions` - Create new session
  - `GET /sessions/{session_id}` - Get session history
  - `DELETE /sessions/{session_id}` - Delete session (optional)
  - `GET /health` - Health check endpoint

#### 6.2 Request/Response Models
- [ ] Create `models/schemas.py`
  - `ChatRequest` - { session_id, question, retrieval_mode, selected_text }
  - `ChatResponse` - { answer, citations, sources, metadata }
  - `SessionResponse` - { session_id, created_at, messages }
  - `HealthResponse` - { status, services: { db, qdrant, llm } }

#### 6.3 Middleware & Error Handling
- [ ] Create `api/middleware.py`
  - CORS configuration (allow frontend origin)
  - Request logging (structured JSON)
  - Error handling middleware (catch exceptions)
  - Rate limiting (optional v2)
- [ ] Create `utils/errors.py`
  - Custom exception classes (RAGError, RetrievalError, etc.)
  - Exception handlers for FastAPI
  - Error response formatting

#### 6.4 Main App
- [ ] Create `main.py`
  - Initialize FastAPI app
  - Register routes
  - Add middleware
  - Configure CORS
  - Add startup/shutdown events (DB connection)

**Output**: Working REST API with all endpoints

**Dependencies**: Phase 2 (storage), Phase 5 (agent)

**API Specifications**:

```python
# POST /chat
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat request and return grounded answer."""
    pass

# POST /sessions
@app.post("/sessions", response_model=SessionResponse)
async def create_session():
    """Create new chat session."""
    pass

# GET /sessions/{session_id}
@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session history."""
    pass

# GET /health
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health."""
    pass
```

---

### Phase 7: Testing & Validation ⏸️

**Duration**: 90 minutes

**Goal**: Write comprehensive tests, validate end-to-end flow, test edge cases

**Tasks**:

#### 7.1 Unit Tests
- [ ] Test database operations (`tests/test_storage.py`)
  - Session CRUD
  - Message persistence
  - Conversation history loading
- [ ] Test services (`tests/test_services.py`)
  - Gemini embeddings
  - Qdrant retrieval
  - OpenRouter LLM calls
- [ ] Test sub-agents (`tests/test_sub_agents.py`)
  - Retrieval logic
  - Answer generation
  - Guardrails validation
  - Memory loading

#### 7.2 Integration Tests
- [ ] Test main agent (`tests/test_agent.py`)
  - End-to-end chat flow
  - Selected text mode
  - Multi-turn conversations
  - Error handling
- [ ] Test API endpoints (`tests/test_api.py`)
  - POST /chat with valid request
  - Session creation and retrieval
  - Health check
  - Error responses (invalid session, etc.)

#### 7.3 Edge Case Testing
- [ ] Test failure scenarios
  - Qdrant connection failure
  - Gemini API quota exceeded
  - OpenRouter rate limit
  - Invalid session ID
  - Empty retrieval results
  - Hallucination detection
- [ ] Test performance
  - Measure latency per endpoint
  - Concurrent request handling
  - Database connection pooling

#### 7.4 Manual QA
- [ ] Test with sample questions
  - "What is ROS 2?" (should retrieve relevant chunks)
  - "How do I build a humanoid robot?" (multi-chunk answer)
  - "Explain vision-language-action" (technical content)
- [ ] Test selected text mode
  - Highlight passage → ask question → answer grounded in selection
- [ ] Test multi-turn conversations
  - Follow-up questions with context
  - Pronoun resolution ("it", "that")

**Output**: Comprehensive test suite with >80% coverage

**Dependencies**: All previous phases

**Test Coverage Goals**:
- Unit tests: 90%+ coverage
- Integration tests: Critical paths covered
- Edge cases: All error scenarios handled

---

### Phase 8: Documentation ⏸️

**Duration**: 60 minutes

**Goal**: Document architecture, API, deployment, troubleshooting

**Tasks**:
- [ ] Create `backend/README.md`
  - Quick start guide
  - API endpoint documentation
  - Environment variable reference
  - Local development setup
  - Testing instructions
- [ ] Create `specs/API_REFERENCE.md`
  - Detailed API specifications
  - Request/response examples
  - Error codes and messages
  - Authentication (if added)
- [ ] Create `specs/ARCHITECTURE.md`
  - System architecture diagram
  - Agent interaction flow
  - Database schema
  - Service dependencies
  - Deployment topology
- [ ] Create `specs/TROUBLESHOOTING.md`
  - Common errors and solutions
  - Debugging tips
  - Log analysis guide
  - Performance optimization
- [ ] Update `specs/TASKS.md`
  - Mark Phase 1-8 as complete
  - Document completion metrics
  - Next steps for production

**Output**: Complete documentation suite

**Dependencies**: All previous phases

---

## Completion Checklist

### Pre-Implementation ⏸️
- [ ] Environment variables configured
- [ ] PostgreSQL database accessible
- [ ] Qdrant collection populated (from Step 1)
- [ ] API keys validated (Gemini, OpenRouter)

### Core Implementation ⏸️
- [ ] Backend directory structure created
- [ ] Database schema and session management
- [ ] External services integrated (Gemini, Qdrant, OpenRouter)
- [ ] Sub-agents implemented (Retrieval, Answer, Guardrails, Memory)
- [ ] Main RAG agent orchestration
- [ ] FastAPI REST API

### Testing & Validation ⏸️
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Edge cases tested
- [ ] Manual QA completed
- [ ] Performance benchmarks met

### Documentation ⏸️
- [ ] README with setup guide
- [ ] API reference
- [ ] Architecture documentation
- [ ] Troubleshooting guide
- [ ] Updated TASKS.md

---

## Time Estimates

| Phase | Estimated | Dependencies |
|-------|-----------|--------------|
| Setup & Configuration | 30 min | None |
| Database & Sessions | 45 min | Phase 1 |
| Services Integration | 60 min | Phase 1 |
| Sub-Agents | 90 min | Phase 2, 3 |
| Main Agent | 45 min | Phase 2, 3, 4 |
| FastAPI REST API | 60 min | Phase 2, 5 |
| Testing & Validation | 90 min | All previous |
| Documentation | 60 min | All previous |
| **Total** | **480 min (8 hours)** | Sequential |

**Recommended Approach**: Implement phases sequentially to ensure dependencies are met.

---

## Critical Path

```
1. Phase 1: Setup (30 min)
   ↓
2. Phase 2: Database (45 min)
   ↓
3. Phase 3: Services (60 min)
   ↓
4. Phase 4: Sub-Agents (90 min)
   ↓
5. Phase 5: Main Agent (45 min)
   ↓
6. Phase 6: FastAPI API (60 min)
   ↓
7. Phase 7: Testing (90 min)
   ↓
8. Phase 8: Documentation (60 min)
   ↓
9. ✅ Step 2 Complete → Ready for Deployment
```

---

## Technology Stack

### Backend Framework
- **FastAPI** - Modern, async Python web framework
- **Uvicorn** - Lightning-fast ASGI server
- **Pydantic** - Data validation using Python type hints

### Database
- **PostgreSQL** - Relational database for session storage
- **SQLAlchemy** - ORM for database operations
- **Psycopg2** - PostgreSQL adapter

### Vector Database
- **Qdrant Cloud** - Vector similarity search (from Step 1)

### LLM & Embeddings
- **Claude 3.5 Sonnet** - Via OpenRouter API
- **Gemini embeddings-001** - 768-dim query embeddings (from Step 1)

### Development Tools
- **Pytest** - Testing framework
- **Black** - Code formatting
- **Flake8** - Linting
- **Mypy** - Type checking (optional)

---

## Success Metrics

- [ ] All API endpoints respond within 2 seconds
- [ ] Zero hallucinations in test set (100% grounded)
- [ ] >80% test coverage
- [ ] Session persistence works across restarts
- [ ] Multi-turn conversations maintain context
- [ ] Selected text mode works correctly
- [ ] Health check reports all services healthy
- [ ] Documentation is clear and complete

---

## Risk Mitigation

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| OpenRouter rate limits | High | Exponential backoff + retry | ⏸️ Planned |
| Gemini quota exhaustion | Medium | Use MockEmbeddings fallback | ✅ Handled (Step 1) |
| Qdrant connection failures | High | Retry logic + circuit breaker | ⏸️ Planned |
| PostgreSQL connection pool exhaustion | Medium | Configure max connections | ⏸️ Planned |
| Hallucination detection false positives | Low | Tune guardrails threshold | ⏸️ Planned |
| Slow LLM response times | Medium | Set timeout + streaming (v2) | ⏸️ Planned |

---

## Dependencies

### External Services
- PostgreSQL database (Neon free tier)
- Qdrant Cloud (populated from Step 1)
- Google Gemini API (embeddings)
- OpenRouter API (Claude 3.5 Sonnet)

### Python Packages (requirements.txt)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
qdrant-client==1.7.0
google-generativeai==0.3.0
httpx==0.25.1
pydantic==2.5.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

### Infrastructure
- Python 3.11+
- PostgreSQL 15+ (or Neon serverless)
- Internet connection (API access)
- 1 GB disk space (logs, cache)

---

## Architectural Decisions

### 1. Why FastAPI?
- **Async/await support**: Non-blocking I/O for concurrent requests
- **Automatic API docs**: Swagger UI out-of-the-box
- **Type safety**: Pydantic validation prevents bugs
- **Performance**: Faster than Flask/Django for I/O-bound workloads

### 2. Why Sub-Agent Architecture?
- **Separation of concerns**: Each sub-agent has single responsibility
- **Testability**: Easier to unit test individual components
- **Extensibility**: Add new sub-agents without modifying orchestrator
- **Debuggability**: Clear trace of which sub-agent caused error

### 3. Why PostgreSQL for Sessions?
- **Reliability**: ACID transactions ensure data consistency
- **Simplicity**: No need for distributed cache (Redis) yet
- **Neon free tier**: Serverless PostgreSQL with zero cost
- **Migration path**: Easy to add caching layer later

### 4. Why OpenRouter for Claude?
- **Cost-effective**: Pay-per-use pricing (no subscription)
- **Reliability**: Multi-provider fallback (Anthropic, AWS)
- **Simplicity**: Single API for multiple models
- **Flexibility**: Easy to swap models (GPT-4, Gemini Pro)

### 5. Why Guardrails Sub-Agent?
- **Zero hallucinations**: Critical for educational content
- **Trust**: Users need confidence in answers
- **Safety**: Prevent spreading misinformation
- **Compliance**: Required for academic/professional use

---

## Implementation Strategy

### Recommended Order
1. **Database first** (Phase 2) - Foundation for everything else
2. **Services next** (Phase 3) - Needed by sub-agents
3. **Sub-agents** (Phase 4) - Core RAG logic
4. **Orchestration** (Phase 5) - Ties everything together
5. **API layer** (Phase 6) - User-facing interface
6. **Testing** (Phase 7) - Validate everything works
7. **Documentation** (Phase 8) - Enable others to use/maintain

### Testing Strategy
- **Test-Driven Development (TDD)**: Write tests before implementation
- **Mocking**: Mock external services (Qdrant, OpenRouter) in unit tests
- **Integration tests**: Use test database and test Qdrant collection
- **End-to-end tests**: Real API calls to verify production behavior

### Error Handling Strategy
- **Custom exceptions**: Create typed exceptions (RetrievalError, LLMError)
- **Graceful degradation**: Return partial results when possible
- **Logging**: Structured JSON logs for debugging
- **User-friendly errors**: Never expose internal error details to users

---

## Next Steps After Completion

### Production Deployment
1. Dockerize backend (create Dockerfile)
2. Deploy to Render (or Railway, Fly.io)
3. Configure environment variables in platform
4. Set up health check monitoring
5. Test deployed endpoints

### Frontend Integration
1. Connect Docusaurus site to backend API
2. Build chat widget component
3. Implement session management in UI
4. Add selected text highlighting
5. Display citations as footnotes

### Performance Optimization
1. Add caching layer (Redis) for embeddings
2. Implement connection pooling for Qdrant
3. Add request queuing for rate limiting
4. Enable response streaming for long answers
5. Optimize database queries (indexes, EXPLAIN)

### Monitoring & Observability
1. Set up logging aggregation (Datadog, Sentry)
2. Add performance metrics (Prometheus)
3. Create alerts for errors/latency
4. Build analytics dashboard
5. Track user satisfaction metrics

---

**Last Updated**: 2026-01-03

**Status**: ⏸️ Awaiting user approval to proceed with implementation

**Next Action**: Review plan → Get approval → Start Phase 1 (Setup)
