# Step 2: RAG Agent - Task Breakdown

## Status: ⏸️ PLANNING PHASE

---

## Phase 1: Project Setup & Configuration ⏸️

**Duration**: 30 minutes

- [ ] Create backend directory structure
- [ ] Create module directories (agent/, rag/, api/, services/, storage/, models/, utils/)
- [ ] Create requirements.txt with all dependencies
- [ ] Install dependencies with pip
- [ ] Configure .env with all API keys and URLs
- [ ] Create .env.example template
- [ ] Verify all environment variables are accessible

**Output**: Configured backend directory with dependencies installed

---

## Phase 2: Database & Session Management ⏸️

**Duration**: 45 minutes

- [ ] Create storage/models.py with SQLAlchemy models
  - Session table (id, created_at, updated_at)
  - Message table (id, session_id, role, content, timestamp)
- [ ] Create storage/init_db.py for database initialization
- [ ] Create storage/sessions.py with CRUD operations
  - create_session()
  - get_session(session_id)
  - save_message(session_id, role, content)
- [ ] Test database connectivity and operations
- [ ] Verify session and message persistence

**Output**: Working PostgreSQL schema with session management

---

## Phase 3: External Services Integration ⏸️

**Duration**: 60 minutes

- [ ] Create services/embeddings.py
  - Reuse GeminiEmbeddings from ingestion/
  - Implement embed_query(text) method
  - Add error handling and rate limiting
- [ ] Create rag/retrieval.py
  - QdrantRetriever class
  - search(query_vector, top_k, score_threshold) method
  - format_results() method
- [ ] Create services/openrouter_service.py
  - OpenRouterClient class
  - generate(messages, max_tokens, temperature) method
  - Retry logic with exponential backoff
  - Token usage tracking
- [ ] Test all three services independently

**Output**: Three working service integrations

---

## Phase 4: RAG Sub-Agents Implementation ⏸️

**Duration**: 90 minutes

- [ ] Create agent/sub_agents.py with RetrievalSubAgent
  - Detect retrieval mode
  - Embed query
  - Search Qdrant
  - Return formatted chunks
- [ ] Implement AnswerSubAgent
  - Construct RAG prompt
  - Call Claude 3.5 Sonnet
  - Parse response
  - Extract citations
- [ ] Implement GuardrailsSubAgent
  - Check grounding
  - Detect hallucinations
  - Validate citations
  - Return validation result
- [ ] Implement MemorySubAgent
  - Load conversation history
  - Format for LLM context
  - Limit to last 10 messages
- [ ] Test each sub-agent independently

**Output**: Four working sub-agents with clear interfaces

---

## Phase 5: Main RAG Agent Orchestration ⏸️

**Duration**: 45 minutes

- [ ] Create agent/agent.py with BookRAGAgent class
- [ ] Implement chat() method with orchestration logic
  - Load conversation history (MemorySubAgent)
  - Retrieve chunks (RetrievalSubAgent)
  - Generate answer (AnswerSubAgent)
  - Validate answer (GuardrailsSubAgent)
  - Save message to session
- [ ] Add error handling at each step
- [ ] Add graceful degradation logic
- [ ] Test end-to-end agent flow

**Output**: Main orchestrator agent coordinating full RAG pipeline

---

## Phase 6: FastAPI REST API ⏸️

**Duration**: 60 minutes

- [ ] Create models/schemas.py with Pydantic models
  - ChatRequest, ChatResponse
  - SessionResponse
  - HealthResponse
- [ ] Create api/routes.py with endpoints
  - POST /chat
  - POST /sessions
  - GET /sessions/{session_id}
  - GET /health
- [ ] Create api/middleware.py
  - CORS configuration
  - Request logging
  - Error handling middleware
- [ ] Create utils/errors.py with custom exceptions
- [ ] Create main.py with FastAPI app
- [ ] Test all API endpoints

**Output**: Working REST API with all endpoints

---

## Phase 7: Testing & Validation ⏸️

**Duration**: 90 minutes

- [ ] Write unit tests for database operations (tests/test_storage.py)
- [ ] Write unit tests for services (tests/test_services.py)
- [ ] Write unit tests for sub-agents (tests/test_sub_agents.py)
- [ ] Write integration tests for main agent (tests/test_agent.py)
- [ ] Write API endpoint tests (tests/test_api.py)
- [ ] Test edge cases and failure scenarios
- [ ] Measure performance and latency
- [ ] Manual QA with sample questions
- [ ] Test selected text mode
- [ ] Test multi-turn conversations
- [ ] Verify >80% test coverage

**Output**: Comprehensive test suite with >80% coverage

---

## Phase 8: Documentation ⏸️

**Duration**: 60 minutes

- [ ] Create backend/README.md with setup guide
- [ ] Create specs/API_REFERENCE.md with endpoint docs
- [ ] Create specs/ARCHITECTURE.md with system diagrams
- [ ] Create specs/TROUBLESHOOTING.md with debugging tips
- [ ] Update specs/STEP_2_TASKS.md to mark phases complete
- [ ] Document all environment variables
- [ ] Add code comments and docstrings

**Output**: Complete documentation suite

---

## Completion Checklist

### Pre-Implementation ⏸️
- [ ] PostgreSQL database accessible
- [ ] Qdrant collection populated (from Step 1)
- [ ] Gemini API key valid
- [ ] OpenRouter API key valid
- [ ] All environment variables configured

### Core Implementation ⏸️
- [ ] Backend directory structure created
- [ ] Database schema and session management working
- [ ] Services integrated (Gemini, Qdrant, OpenRouter)
- [ ] Sub-agents implemented and tested
- [ ] Main RAG agent orchestration working
- [ ] FastAPI REST API running

### Testing ⏸️
- [ ] Unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] Edge cases tested
- [ ] Manual QA completed
- [ ] Performance benchmarks met

### Documentation ⏸️
- [ ] README complete
- [ ] API reference complete
- [ ] Architecture docs complete
- [ ] Troubleshooting guide complete

---

## Time Estimates

| Phase | Estimated | Actual | Status |
|-------|-----------|--------|--------|
| Setup & Configuration | 30 min | - | ⏸️ Pending |
| Database & Sessions | 45 min | - | ⏸️ Pending |
| Services Integration | 60 min | - | ⏸️ Pending |
| Sub-Agents | 90 min | - | ⏸️ Pending |
| Main Agent | 45 min | - | ⏸️ Pending |
| FastAPI REST API | 60 min | - | ⏸️ Pending |
| Testing & Validation | 90 min | - | ⏸️ Pending |
| Documentation | 60 min | - | ⏸️ Pending |
| **Total** | **480 min (8 hours)** | **0 min** | **0% done** |

---

## Critical Path

```
⏸️ 1. Setup backend directory and dependencies
   ↓
⏸️ 2. Set up PostgreSQL schema and session management
   ↓
⏸️ 3. Integrate external services (Gemini, Qdrant, OpenRouter)
   ↓
⏸️ 4. Implement sub-agents (Retrieval, Answer, Guardrails, Memory)
   ↓
⏸️ 5. Build main RAG agent orchestrator
   ↓
⏸️ 6. Create FastAPI REST API
   ↓
⏸️ 7. Write and run comprehensive tests
   ↓
⏸️ 8. Document architecture and API
   ↓
⏸️ 9. Step 2 Complete → Ready for Deployment
```

---

## Risk Mitigation

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| OpenRouter rate limits | High | Exponential backoff + retry | ⏸️ Planned |
| Gemini quota exhaustion | Medium | MockEmbeddings fallback | ✅ Handled |
| Qdrant connection failures | High | Retry logic + circuit breaker | ⏸️ Planned |
| PostgreSQL connection issues | Medium | Connection pooling | ⏸️ Planned |
| Hallucination false positives | Low | Tune guardrails threshold | ⏸️ Planned |

---

## Success Metrics

- [ ] All API endpoints respond within 2 seconds
- [ ] Zero hallucinations in test set (100% grounded)
- [ ] >80% test coverage
- [ ] Session persistence across restarts
- [ ] Multi-turn conversations maintain context
- [ ] Selected text mode works correctly
- [ ] Health check reports all services healthy

**Current Progress**: 0% (0/7 metrics met)

---

**Last Updated**: 2026-01-03

**Status**: ⏸️ Awaiting user approval to proceed

**Next Action**: Review plan → Get approval → Start Phase 1
