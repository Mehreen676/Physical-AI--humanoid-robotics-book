# Agentic RAG - Task Breakdown

## Status: 📋 **PLANNING PHASE**

**Duration**: 3.5 hours (210 minutes)

---

## Phase 1: Neon Postgres Setup ⏸️

**Duration**: 30 minutes

- [ ] Create Neon Serverless Postgres account
- [ ] Create new database project
- [ ] Get connection string (DATABASE_URL)
- [ ] Add DATABASE_URL to .env
- [ ] Create `backend/storage/database.py`
- [ ] Implement database schema:
  - [ ] sessions table (id, user_id, created_at)
  - [ ] chat_turns table (id, session_id, question, answer, etc.)
  - [ ] idx_session_turns index
- [ ] Implement NeonDatabase class:
  - [ ] `__init__` with connection management
  - [ ] `_init_schema()` to create tables
  - [ ] `create_session(user_id)`
  - [ ] `add_turn(...)` to store chat turn
  - [ ] `get_conversation_history(session_id)`
  - [ ] `session_exists(session_id)`
- [ ] Test database connection
- [ ] Test session CRUD operations
- [ ] Test turn storage and retrieval

**Output**: Working Neon Postgres with schema and CRUD operations

---

## Phase 2: ChatKit Agent Integration ⏸️

**Duration**: 60 minutes

### 2.1 Agent Configuration (20 min)
- [ ] Install OpenAI SDK: `pip install openai`
- [ ] Add OPENAI_API_KEY to .env
- [ ] Create `backend/agent/chatkit_agent.py`
- [ ] Implement ChatKitAgent class:
  - [ ] `__init__(api_key)` with OpenAI client
  - [ ] `get_system_instructions()` with grounding rules
  - [ ] `create_chat_completion(question, context, history)`
- [ ] Set temperature=0 for determinism
- [ ] Test agent initialization
- [ ] Test system instructions content

### 2.2 Context Formatting (20 min)
- [ ] Create `backend/agent/context_formatter.py`
- [ ] Implement ContextFormatter class:
  - [ ] `format_chunks(chunks)` → formatted context
  - [ ] `format_selected_text_context(selected_text, chunks)`
  - [ ] `get_context_token_count(context)` → estimate
  - [ ] `truncate_if_needed(context, max_tokens)`
- [ ] Test chunk formatting with sample data
- [ ] Test empty chunks handling
- [ ] Test token counting accuracy
- [ ] Test truncation logic

### 2.3 Selected-Text Handler (20 min)
- [ ] Create `backend/agent/selected_text_handler.py`
- [ ] Implement SelectedTextHandler class:
  - [ ] `validate_selected_text(text, mode)` with ValueError
  - [ ] `prepare_selected_text_context(question, text, chunks)`
  - [ ] `verify_answer_scope(answer, selected_text)`
- [ ] Test validation (required, min/max length)
- [ ] Test context preparation
- [ ] Test answer scope verification

**Output**: ChatKit agent configured with context formatting and selected-text support

---

## Phase 3: Answer Generation & Refusal ⏸️

**Duration**: 45 minutes

### 3.1 Answer Generator (25 min)
- [ ] Create `backend/agent/answer_generator.py`
- [ ] Implement AnswerGenerator class:
  - [ ] `__init__(agent)` with ChatKitAgent instance
  - [ ] `generate_answer(question, context, history)` → dict
  - [ ] `_is_refusal(answer)` → bool
  - [ ] `extract_citations(answer, chunks)` → List[Citation]
  - [ ] `validate_grounding(answer, chunks)` → bool
- [ ] Test answer generation with sample context
- [ ] Test refusal detection
- [ ] Test citation extraction
- [ ] Test grounding validation

### 3.2 Error Handling & Logging (20 min)
- [ ] Create `backend/utils/error_handling.py`
- [ ] Define custom exceptions:
  - [ ] RetrievalError
  - [ ] AgentError
  - [ ] DatabaseError
  - [ ] ValidationError
- [ ] Implement `@handle_errors` decorator
- [ ] Create `backend/utils/logging.py`
- [ ] Implement StructuredLogger:
  - [ ] `log_event(event, level, **kwargs)`
  - [ ] `log_latency(operation, latency_ms)`
- [ ] Test error handling decorator
- [ ] Test structured logging output

**Output**: Answer generation with refusal handling, error handling, and logging

---

## Phase 4: API Orchestration ⏸️

**Duration**: 45 minutes

### 4.1 Update Configuration (10 min)
- [ ] Update `backend/config.py`:
  - [ ] Add `openai_api_key` field
  - [ ] Add `database_url` field
  - [ ] Remove `openrouter_api_key` (not needed)
  - [ ] Update `validate_required()` method
- [ ] Update `.env` with new variables
- [ ] Test configuration loading

### 4.2 Update Chat Endpoint (30 min)
- [ ] Update `backend/api/routes.py`
- [ ] Modify POST `/chat` endpoint:
  - [ ] Import new agent components
  - [ ] Validate selected text if needed
  - [ ] Call retrieval layer (keep existing)
  - [ ] Format context using ContextFormatter
  - [ ] Get conversation history from Neon
  - [ ] Initialize ChatKitAgent
  - [ ] Generate answer using AnswerGenerator
  - [ ] Extract citations
  - [ ] Store turn in Neon Postgres
  - [ ] Return ChatResponse
- [ ] Add error handling with @handle_errors
- [ ] Add structured logging for all steps
- [ ] Test endpoint with mock data
- [ ] Test with real retrieval + agent

### 4.3 Update Other Endpoints (5 min)
- [ ] Update POST `/sessions`:
  - [ ] Use NeonDatabase.create_session()
- [ ] Update GET `/sessions/{id}`:
  - [ ] Use NeonDatabase.get_conversation_history()
- [ ] Test session endpoints

**Output**: Updated FastAPI endpoints using ChatKit agent and Neon storage

---

## Phase 5: Testing & Validation ⏸️

**Duration**: 45 minutes

### 5.1 Unit Tests (15 min)
- [ ] Create `tests/test_chatkit_agent.py`:
  - [ ] test_agent_initialization
  - [ ] test_system_instructions
  - [ ] test_chat_completion (with mock)
- [ ] Create `tests/test_context_formatter.py`:
  - [ ] test_format_chunks
  - [ ] test_empty_chunks
  - [ ] test_selected_text_formatting
  - [ ] test_token_counting
- [ ] Create `tests/test_database.py`:
  - [ ] test_create_session
  - [ ] test_add_turn
  - [ ] test_get_history
- [ ] Run: `pytest tests/ -v`

### 5.2 Integration Tests (15 min)
- [ ] Create `tests/test_agentic_rag_integration.py`:
  - [ ] test_full_chat_flow (retrieval → agent → storage)
  - [ ] test_deterministic_responses
  - [ ] test_conversation_continuity
- [ ] Test normal mode end-to-end
- [ ] Test selected-text mode end-to-end
- [ ] Run all integration tests

### 5.3 Grounding Validation (10 min)
- [ ] Create `tests/test_grounding.py`:
  - [ ] test_grounded_answer
  - [ ] test_refusal_out_of_scope
  - [ ] test_no_hallucination
  - [ ] test_citation_accuracy
- [ ] Run grounding tests with real agent
- [ ] Verify no external knowledge used
- [ ] Verify refusal behavior

### 5.4 Manual QA (5 min)
- [ ] Test 5+ sample questions:
  - [ ] "What is ROS 2?" (normal mode)
  - [ ] "How does DDS work?" (normal mode)
  - [ ] Selected-text: "DDS is used..." → "Explain this"
  - [ ] Out-of-scope: "What is quantum computing?"
  - [ ] Follow-up: "Tell me more about that"
- [ ] Verify all answers grounded
- [ ] Verify refusals for out-of-scope
- [ ] Verify citations present
- [ ] Check conversation history stored

**Output**: Comprehensive test coverage with validated grounding

---

## Phase 6: Documentation ⏸️

**Duration**: 30 minutes

- [ ] Create `backend/CHATKIT_AGENT_GUIDE.md`:
  - [ ] Overview and architecture
  - [ ] Agent configuration details
  - [ ] Grounding rules explanation
  - [ ] Context formatting examples
  - [ ] Selected-text mode guide
  - [ ] Testing guide
  - [ ] Troubleshooting
- [ ] Update `backend/README.md`:
  - [ ] Add ChatKit agent section
  - [ ] Update environment variables
  - [ ] Add Neon Postgres setup
  - [ ] Update API examples
- [ ] Create `backend/DEPLOYMENT.md`:
  - [ ] Neon Postgres setup steps
  - [ ] Environment variable checklist
  - [ ] Railway/Render deployment
  - [ ] Health check verification
- [ ] Add inline docstrings to all new files
- [ ] Create example requests in README

**Output**: Complete documentation for agentic RAG system

---

## Completion Checklist

### Pre-Implementation ⏸️
- [ ] Retrieval layer complete (Step 1 & 2) ✅
- [ ] Neon Postgres account created
- [ ] OpenAI API key obtained
- [ ] Environment variables configured

### Core Implementation ⏸️
- [ ] Neon Postgres schema created
- [ ] ChatKit agent configured
- [ ] Context formatting working
- [ ] Selected-text handler implemented
- [ ] Answer generation working
- [ ] Error handling & logging added
- [ ] API endpoints updated
- [ ] Integration with retrieval layer

### Testing ⏸️
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration tests passing
- [ ] Grounding validation passing
- [ ] Manual QA completed
- [ ] Determinism verified
- [ ] Performance acceptable (<3s P95)

### Documentation ⏸️
- [ ] Agent configuration guide
- [ ] API documentation updated
- [ ] Deployment guide created
- [ ] Examples and troubleshooting

---

## Time Estimates

| Phase | Estimated | Actual | Status |
|-------|-----------|--------|--------|
| Neon Postgres Setup | 30 min | - | ⏸️ Pending |
| ChatKit Agent Integration | 60 min | - | ⏸️ Pending |
| Answer Generation & Refusal | 45 min | - | ⏸️ Pending |
| API Orchestration | 45 min | - | ⏸️ Pending |
| Testing & Validation | 45 min | - | ⏸️ Pending |
| Documentation | 30 min | - | ⏸️ Pending |
| **Total** | **210 min (3.5 hours)** | **0 min** | **0% done** |

---

## Critical Path

```
⏸️ 1. Neon Postgres Setup (30 min)
   ↓
⏸️ 2. ChatKit Agent Integration (60 min)
   ↓
⏸️ 3. Answer Generation & Refusal (45 min)
   ↓
⏸️ 4. API Orchestration (45 min)
   ↓
⏸️ 5. Testing & Validation (45 min)
   ↓
⏸️ 6. Documentation (30 min)
   ↓
✅ Agentic RAG Complete → Production Ready
```

---

## Success Metrics

- [ ] Agent answers grounded 100% in retrieved content
- [ ] 0 hallucinated facts or citations
- [ ] Selected-text mode restricts context correctly
- [ ] Chat history persisted in Neon Postgres
- [ ] API response time <3 seconds (P95)
- [ ] Clear refusal when context insufficient
- [ ] Deterministic responses (same input → same output)
- [ ] Conversation history retrievable

**Current Progress**: 0% (0/8 metrics met)

---

## Risk Mitigation

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| OpenAI API costs | Medium | Monitor usage, set budget alerts | ⏸️ Planned |
| Neon Postgres limits | Low | Free tier sufficient for MVP | ⏸️ Monitored |
| Agent hallucination | High | Strict system instructions, validation | ⏸️ Planned |
| Slow agent responses | Medium | Timeout at 5s, log latency | ⏸️ Planned |
| Database connection issues | Medium | Connection pooling, retry logic | ⏸️ Planned |

---

## Dependencies

### External Services
- **Neon Serverless Postgres**: Chat history storage
- **OpenAI API**: ChatKit agent runtime
- **Qdrant Cloud**: Vector search (already setup ✅)
- **Gemini API**: Embeddings (already setup ✅)

### Python Packages
```
openai==1.3.0           # OpenAI Agents SDK
psycopg2-binary==2.9.9  # Postgres driver
python-dotenv==1.0.0    # Already installed ✅
pydantic==2.5.0         # Already installed ✅
fastapi==0.104.1        # Already installed ✅
```

### Completed Components (Reuse)
- ✅ `retrieval/` module (semantic search)
- ✅ FastAPI app structure
- ✅ Request/response schemas
- ✅ Environment configuration

---

## Integration with Existing System

### Keep Unchanged ✅
- `retrieval/` module (no changes)
- FastAPI app structure
- API endpoint paths
- Request/response schemas
- CORS configuration

### Replace 🔄
- `backend/services/claude_service.py` → `backend/agent/chatkit_agent.py`
- `backend/storage/sessions.py` (in-memory) → `backend/storage/database.py` (Neon)
- `backend/agent/sub_agents.py` → Simplified with ChatKit

### Update 🔄
- `backend/api/routes.py` (new orchestration flow)
- `backend/config.py` (add OPENAI_API_KEY, DATABASE_URL)
- `backend/requirements.txt` (add openai, psycopg2-binary)
- `.env` (add new environment variables)

---

## File Structure

```
backend/
├── agent/
│   ├── chatkit_agent.py          NEW
│   ├── context_formatter.py      NEW
│   ├── selected_text_handler.py  NEW
│   └── answer_generator.py       NEW
├── storage/
│   └── database.py                NEW (replaces sessions.py)
├── utils/
│   ├── error_handling.py         NEW
│   └── logging.py                NEW
├── api/
│   └── routes.py                 UPDATE
├── config.py                     UPDATE
├── requirements.txt              UPDATE
├── CHATKIT_AGENT_GUIDE.md        NEW
└── DEPLOYMENT.md                 NEW

tests/
├── test_chatkit_agent.py         NEW
├── test_context_formatter.py     NEW
├── test_database.py              NEW
├── test_agentic_rag_integration.py  NEW
└── test_grounding.py             NEW
```

---

**Last Updated**: 2026-01-03

**Status**: ⏸️ Planning complete, awaiting implementation approval

**Next Action**: Start Phase 1 (Neon Postgres Setup)

**Estimated Completion**: 3.5 hours from start
