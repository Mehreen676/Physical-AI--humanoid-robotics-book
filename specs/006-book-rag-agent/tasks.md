# Tasks: BookRAGAgent — Multi-Agent Orchestration for Hallucination-Free RAG

**Input**: Design documents from `/specs/006-book-rag-agent/`
**Prerequisites**: plan.md (complete), spec.md (complete), data-model.md (complete), contracts/ (complete)
**Status**: Ready for Implementation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Each user story is an independently deployable MVP increment.

---

## Format: `[ID] [P?] [Story] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete prior tasks)
- **[Story]**: User story label (US1, US2, US3, US4) - REQUIRED for story tasks, NOT for setup/foundational tasks
- **Checkbox**: Always `- [ ]` (unchecked)
- **Task ID**: Sequential (T001, T002, etc.)

---

## Phase 1: Project Setup (Shared Infrastructure)

**Purpose**: Initialize project structure, dependencies, and configuration foundation

**Checkpoint**: After this phase, basic FastAPI server runs and connects to all external services

---

- [ ] T001 Create Python project structure per implementation plan in /backend directory (create folders: agent/, rag/, storage/, models/, api/, services/)

- [ ] T002 Create requirements.txt in /backend with all dependencies: fastapi, uvicorn, openai-agent-sdk, chatkit-sdk, qdrant-client, psycopg2-binary, pydantic, python-dotenv, pytest, pytest-asyncio, pytest-cov

- [ ] T003 Create /backend/main.py with FastAPI application initialization, ASGI server setup, and root route

- [ ] T004 Create /backend/config.py for environment variable loading and validation (validate OPENROUTER_API_KEY, QDRANT_API_KEY, QDRANT_URL, DATABASE_URL, COLLECTION_NAME, OPENROUTER_URL, MODEL_NAME, BASE_URL at startup)

- [ ] T005 Create /backend/.env.example with placeholder values for all environment variables (NEVER commit actual .env)

- [ ] T006 [P] Create /backend/__init__.py files for all packages (agent/, rag/, storage/, models/, api/, services/)

- [ ] T007 Create /backend/pyproject.toml with project metadata, version 1.0.0, Python 3.11+ requirement

- [ ] T008 Create tests/ directory structure with __init__.py, unit/, integration/, fixtures/ subdirectories

- [ ] T009 Create tests/conftest.py for pytest configuration, fixtures, and async test support

- [ ] T010 [P] Create tests/fixtures/ directory with mock data files: mock_qdrant.py (sample chunks), mock_openrouter.py (sample LLM responses), sample_chunks.py (test book chunks)

**Checkpoint**: Project structure ready, dependencies installable, environment validation working

---

## Phase 2: Foundational Layer (Blocking Prerequisites)

**Purpose**: Build core infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: NO user story work can begin until this phase completes

---

### Data Models & Schemas

- [ ] T011 Create /backend/models/schemas.py with Pydantic models: ChatRequest (question, session_id, selected_text), Citation (section, url), RetrievedChunkResponse (text, metadata), ChatResponse (answer, citations, retrieved_chunks)

- [ ] T012 Create /backend/models/schemas.py additions: SessionCreateResponse (session_id, created_at), SessionGetResponse (session_id, messages), HealthResponse (status, services), ErrorResponse (error, message)

- [ ] T013 [P] Create /backend/storage/models.py with SQLAlchemy ORM models: User (user_id, created_at), Session (session_id, user_id, created_at, updated_at, metadata), ChatMessage (message_id, session_id, role, content, metadata, created_at)

- [ ] T014 Create /backend/storage/models.py with database relationships, foreign keys, indexes (user_id FK, session_id FK), and trigger for auto-updating session.updated_at

### Database Setup

- [ ] T015 Create /backend/storage/init_db.py with function to initialize database schema from SQLAlchemy models (create tables, indexes, relationships)

- [ ] T016 Create /backend/storage/sessions.py with SessionManager class: create_session(user_id), get_session(session_id), add_message(session_id, role, content, metadata), get_messages(session_id, limit=5)

- [ ] T017 [P] Create tests/unit/test_sessions.py with unit tests for SessionManager (test create_session, test get_messages, test add_message) using mocked database

### External Service Integration

- [ ] T018 Create /backend/services/openrouter_service.py with OpenRouterClient class: __init__(api_key, model_name), call(prompt, temperature=0.7, max_tokens=2000) returning structured response with content and usage

- [ ] T019 Create /backend/services/embeddings.py with EmbeddingsService class (interface for Cohere or compatible): embed(text) returning embedding vector, embed_batch(texts) for multiple texts

- [ ] T020 Create /backend/rag/retrieval.py with QdrantClient wrapper: connect(qdrant_url, api_key), search(query_vector, collection_name, top_k=5) returning chunks with metadata, health_check() returning status

- [ ] T021 [P] Create tests/unit/test_openrouter_service.py with mocked OpenRouter API responses; test call(), test error handling for timeout/invalid API key

- [ ] T022 [P] Create tests/unit/test_embeddings.py with mocked embedding responses; test embed(), test embed_batch(), test error handling

- [ ] T023 [P] Create tests/unit/test_retrieval.py with mocked Qdrant responses; test search(), test metadata preservation, test health_check()

### Logging & Error Handling

- [ ] T024 Create /backend/utils/logging.py with structured logging setup: JSON format for production, colored format for development; NEVER log API keys or secrets

- [ ] T025 Create /backend/utils/errors.py with custom exception classes: RAGError (base), HallucinationDetectedException, RetrievalFailedException, ServiceUnavailableException with user-friendly messages

- [ ] T026 Create /backend/api/middleware.py with request/response logging middleware and error handler that converts exceptions to JSON responses with correct HTTP status codes

### Configuration

- [ ] T027 Create /backend/utils/validators.py with input validation functions: validate_question(text, max_length=500), validate_session_id(session_id), validate_selected_text(text), sanitize_input(text)

**Checkpoint**: All external services connected with mocked responses, database schema ready, error handling in place, logging configured, tests passing

---

## Phase 3: User Story 1 - Full RAG Pipeline (Priority: P1) 🎯 MVP

**Goal**: Core functionality - user submits query, system returns grounded answer with citations and retrieved chunks

**Independent Test**: Can be fully tested by submitting a query to /chat endpoint, verifying structured response with answer, citations, and retrieved_chunks

**Acceptance Criteria**:
- ✓ VectorSearchSkill retrieves relevant chunks from Qdrant with metadata preserved
- ✓ GroundedSynthesisSkill synthesizes answer exclusively from chunks
- ✓ AntiHallucinationSkill detects and vetos hallucinations
- ✓ /chat endpoint returns correct JSON structure
- ✓ All skills execute in correct order

---

### Skill Implementations for Story 1

- [ ] T028 [P] Create /backend/agent/skills.py base class Skill with execute(input) interface

- [ ] T029 Create /backend/rag/retrieval.py with VectorSearchSkill class: execute(query_text, retrieval_mode='normal', top_k=5) → returns RetrievedChunk list with metadata

- [ ] T030 Create /backend/rag/grounding.py with GroundedSynthesisSkill class: execute(chunks, query_text, llm_client) → synthesizes answer from chunks only (prompt includes anti-hallucination instructions)

- [ ] T031 Create /backend/rag/grounding.py with AntiHallucinationSkill class: execute(answer, original_chunks, llm_client) → validates answer against chunks, returns veto if hallucination detected, else returns answer

- [ ] T032 Create /backend/rag/grounding.py with RetrievalValidationSkill class: execute(chunks) → validates chunk metadata integrity, returns cleaned chunks or raises error if validation fails

### Sub-Agent Implementations for Story 1

- [ ] T033 [P] Create /backend/agent/sub_agents.py with SubAgentBase class and registry for managing sub-agent instances

- [ ] T034 Create /backend/agent/sub_agents.py with RetrievalSubAgent class: accepts query, calls VectorSearchSkill, returns chunks

- [ ] T035 Create /backend/agent/sub_agents.py with AnswerSubAgent class: accepts chunks and query, calls GroundedSynthesisSkill, returns synthesized answer

- [ ] T036 Create /backend/agent/sub_agents.py with GuardrailsSubAgent class: accepts answer and chunks, calls RetrievalValidationSkill and AntiHallucinationSkill in sequence, returns veto or approved answer

### Main Agent Orchestration for Story 1

- [ ] T037 Create /backend/agent/agent.py with BookRAGAgent class: orchestrates execution flow (SelectionMode → Retrieval → Guardrails → Answer → Guardrails)

- [ ] T038 Create /backend/agent/agent.py with BookRAGAgent.execute(query_request) method implementing execution flow: parse query → retrieval → validation → synthesis → hallucination check → return response or fallback

- [ ] T039 Create /backend/agent/agent.py with fallback response handling: if no chunks found OR hallucination detected, return standard fallback message

### API Endpoint for Story 1

- [ ] T040 Create /backend/api/routes.py with POST /chat endpoint: accepts ChatRequest (question, session_id, selected_text), calls BookRAGAgent.execute(), returns ChatResponse JSON

- [ ] T041 Create /backend/api/routes.py with /chat error handling: catch RAGError exceptions and return appropriate JSON error responses with correct HTTP status codes

### Tests for Story 1

- [ ] T042 [P] Create tests/integration/test_agent_orchestration.py with full agent flow test: submit query → verify chunks retrieved → verify answer synthesized → verify no hallucination → verify response structure

- [ ] T043 [P] Create tests/integration/test_chat_endpoint.py with /chat endpoint test: POST request → verify 200 response → verify ChatResponse schema (answer, citations, retrieved_chunks)

- [ ] T044 [P] Create tests/unit/test_grounding.py with GroundedSynthesisSkill tests: test synthesis from chunks, test that answer references chunk content

- [ ] T045 [P] Create tests/unit/test_anti_hallucination.py with AntiHallucinationSkill tests: test detection of hallucinations, test veto when hallucination found, test approval when grounded

**Checkpoint**: User Story 1 fully functional; /chat endpoint works end-to-end with mocked services; all tests pass (≥80% code coverage for core skills)

---

## Phase 4: User Story 2 - Selected-Text-Only Mode (Priority: P1)

**Goal**: User can highlight passage and ask "answer only from this passage"; system restricts retrieval to that passage

**Independent Test**: Submit query with selected_text parameter, verify RetrievalSubAgent returns only chunks from that passage, verify answer grounded in that passage only

**Acceptance Criteria**:
- ✓ SelectionModeSubAgent intercepts query and detects selected_text parameter
- ✓ SelectedTextOverrideSkill overrides VectorSearchSkill retrieval scope
- ✓ VectorSearchSkill returns only chunks matching passage_id
- ✓ Answer synthesized entirely from selected passage OR explicitly states "Not found in selected passage"

---

### Skill Implementations for Story 2

- [ ] T046 Create /backend/services/text_selection.py with SelectedTextOverrideSkill class: execute(query_text, selected_text, selected_passage_id) → returns filtered retrieval scope (filter object for Qdrant metadata filtering)

- [ ] T047 Create /backend/rag/retrieval.py enhancement: VectorSearchSkill support for retrieval_mode parameter ('normal' vs 'selected_text') and optional passage_filter

### Sub-Agent Implementations for Story 2

- [ ] T048 Create /backend/agent/sub_agents.py with SelectionModeSubAgent class: accepts query_request with optional selected_text parameter, calls SelectedTextOverrideSkill if present, returns modified retrieval scope

- [ ] T049 Create /backend/agent/sub_agents.py modification: RetrievalSubAgent now accepts optional passage_filter from SelectionModeSubAgent

### Agent Flow Modification for Story 2

- [ ] T050 Create /backend/agent/agent.py enhancement: modify BookRAGAgent.execute() to call SelectionModeSubAgent BEFORE RetrievalSubAgent

- [ ] T051 Create /backend/agent/agent.py: handle "Not found in selected passage" response variant when selected_text mode active and no chunks found

### API Endpoint Modification for Story 2

- [ ] T052 Create /backend/api/routes.py enhancement: /chat endpoint already accepts selected_text parameter (from ChatRequest schema) - pass through to BookRAGAgent

### Tests for Story 2

- [ ] T053 [P] Create tests/integration/test_selected_text_mode.py with selected text constraint test: submit query with selected_text → verify only chunks from that passage returned → verify answer grounded in passage

- [ ] T054 [P] Create tests/unit/test_selection_mode.py with SelectionModeSubAgent tests: test passage_filter generation, test retrieval scope override

- [ ] T055 [P] Create tests/unit/test_retrieval_filtered.py with VectorSearchSkill filtered search tests: test search with passage_filter, verify metadata filtering

**Checkpoint**: User Story 2 fully functional; selected-text mode works end-to-end; Story 1 still passing (no regression)

---

## Phase 5: User Story 3 - Multi-Turn Sessions (Priority: P2)

**Goal**: User can maintain conversation over multiple turns; MemorySubAgent retrieves prior context without contaminating retrieval

**Independent Test**: Submit Q1 → receive A1 → submit Q2 → verify prior context available → verify answer uses context but retrieval still from book only

**Acceptance Criteria**:
- ✓ SessionPersistenceSkill stores messages deterministically in Neon PostgreSQL
- ✓ MemorySubAgent retrieves recent N messages for context
- ✓ Prior context passed to LLM prompt but NOT used for vector search
- ✓ /sessions and /sessions/{id} endpoints work correctly

---

### Skill Implementations for Story 3

- [ ] T056 Create /backend/agent/skills.py with SessionPersistenceSkill class: execute(session_id, message_object, role) → persists to database, returns persistence_result

### Sub-Agent Implementations for Story 3

- [ ] T057 Create /backend/agent/sub_agents.py with MemorySubAgent class: accepts session_id, retrieves recent N messages (e.g., last 5), formats as context for LLM prompt

- [ ] T058 Create /backend/agent/sub_agents.py modification: AnswerSubAgent now accepts optional prior_context parameter from MemorySubAgent, includes in LLM prompt (but NOT in retrieval)

### Agent Flow Modification for Story 3

- [ ] T059 Create /backend/agent/agent.py enhancement: after answer generation, call SessionPersistenceSkill to store user message and assistant response

- [ ] T060 Create /backend/agent/agent.py modification: before generating answer, call MemorySubAgent to retrieve prior context and pass to AnswerSubAgent

### API Endpoints for Story 3

- [ ] T061 Create /backend/api/routes.py with POST /sessions endpoint: creates new session, returns SessionCreateResponse (session_id, created_at)

- [ ] T062 Create /backend/api/routes.py with GET /sessions/{session_id} endpoint: retrieves session with message history, returns SessionGetResponse (session_id, messages list ordered by created_at)

### Tests for Story 3

- [ ] T063 [P] Create tests/integration/test_sessions.py with session creation test: POST /sessions → verify 201 response, verify session_id is valid UUID

- [ ] T064 [P] Create tests/integration/test_session_history.py with multi-turn test: create session → submit Q1 → submit Q2 → verify both messages stored → GET /sessions → verify message list

- [ ] T065 [P] Create tests/unit/test_memory_sub_agent.py with context retrieval tests: test retrieve recent N messages, test formatting for LLM prompt, test isolation (context not used for search)

- [ ] T066 [P] Create tests/unit/test_persistence_skill.py with storage tests: test persist message, test retrieve messages, test deterministic retrieval

**Checkpoint**: User Story 3 fully functional; multi-turn conversation working; Sessions 1-2 still passing

---

## Phase 6: User Story 4 - Fallback & Graceful Degradation (Priority: P1)

**Goal**: When answer cannot be grounded in content, system returns clear fallback message (never hallucination)

**Independent Test**: Query for off-topic content → verify fallback message returned, NOT hallucinated answer

**Acceptance Criteria**:
- ✓ No relevant chunks (below similarity threshold) → fallback: "The answer cannot be found in the provided book content"
- ✓ Hallucination detected by AntiHallucinationSkill → fallback message
- ✓ Qdrant service down → graceful: "The book is not yet indexed. Please try again later."
- ✓ LLM service timeout → graceful: "Unable to process request. Please try again."

---

### Error Handling Enhancements for Story 4

- [ ] T067 Create /backend/rag/retrieval.py enhancement: VectorSearchSkill returns empty list if similarity threshold < 0.7 OR no chunks found (doesn't raise exception)

- [ ] T068 Create /backend/agent/agent.py enhancement: detect empty chunk list, immediately return fallback message without calling LLM

- [ ] T069 Create /backend/api/routes.py enhancement: /health endpoint implemented: checks Qdrant connectivity, database connectivity, OpenRouter API key validity, returns HealthResponse with service statuses

### Service Failure Handling for Story 4

- [ ] T070 Create /backend/rag/retrieval.py enhancement: VectorSearchSkill gracefully handles Qdrant timeout/unavailability, logs error (no secrets), raises ServiceUnavailableException

- [ ] T071 Create /backend/services/openrouter_service.py enhancement: OpenRouterClient handles timeout (30s default), returns error response object (not exception), allowing guardrails to veto

- [ ] T072 Create /backend/storage/sessions.py enhancement: SessionManager handles database connection errors gracefully, logs without exposing credentials, allows /chat to proceed without session storage if DB temporarily down

### Guardrails Validation Enhancements for Story 4

- [ ] T073 Create /backend/rag/grounding.py enhancement: AntiHallucinationSkill logs detected hallucinations with query and proposed answer for debugging (without logging full chunks due to size)

- [ ] T074 Create /backend/agent/agent.py: implement fallback message generation function that returns appropriate message based on failure reason (no chunks, hallucination detected, service error)

### API Response Handling for Story 4

- [ ] T075 Create /backend/api/middleware.py enhancement: catch all exceptions, return JSON error responses: 400 for invalid input, 500 for service errors, never expose internal details

- [ ] T076 Create /backend/api/routes.py enhancement: /chat endpoint catches ServiceUnavailableException and returns 500 with user-friendly message

### Tests for Story 4

- [ ] T077 [P] Create tests/integration/test_fallback.py with off-topic query test: submit query with no relevant content → verify fallback message returned (not hallucination)

- [ ] T078 [P] Create tests/integration/test_service_failures.py with Qdrant down test: mock Qdrant unavailable → verify graceful error response

- [ ] T079 [P] Create tests/integration/test_service_failures.py addition: mock OpenRouter timeout → verify graceful error response

- [ ] T080 [P] Create tests/unit/test_error_handling.py with exception handling tests: test ServiceUnavailableException, test HallucinationDetectedException, test error response formatting

- [ ] T081 [P] Create tests/integration/test_health_endpoint.py with /health endpoint test: verify all service statuses returned correctly

**Checkpoint**: User Story 4 fully functional; graceful fallback working for all failure scenarios; all Stories 1-3 still passing

---

## Phase 7: Integration & Cross-Story Validation

**Purpose**: Ensure all stories work together, no regressions, full end-to-end flows

---

- [ ] T082 Create tests/integration/test_full_workflows.py with multi-story test: create session → query with normal mode → query with selected text → query with context → verify all stories work together

- [ ] T083 [P] Create tests/integration/test_concurrent_sessions.py with concurrency test: multiple sessions simultaneously → verify isolation, no message leakage between sessions

- [ ] T084 [P] Create tests/integration/test_metadata_preservation.py with metadata test: retrieve chunks → verify all metadata (url, section, chunk_id) returned in response and stored in session

- [ ] T085 [P] Create tests/integration/test_response_schema_validation.py with response format test: all endpoints return correct schema per OpenAPI spec (chat-api.openapi.json)

---

## Phase 8: Documentation & Polish

**Purpose**: Ensure system is documented, deployable, and production-ready

---

### Documentation

- [ ] T086 Create /backend/README.md with architecture overview: agent diagram, skills diagram, execution flow description

- [ ] T087 Create /backend/ARCHITECTURE.md with detailed design decisions, data flow diagrams, component interactions

- [ ] T088 [P] Create /backend/API_GUIDE.md with API endpoint documentation, request/response examples, error codes

- [ ] T089 [P] Create /backend/DEPLOYMENT.md with Docker setup, environment variable configuration, scaling guidance

### Code Quality

- [ ] T090 Run black code formatter on all Python files: `black backend/ tests/`

- [ ] T091 Run flake8 linter and fix issues: `flake8 backend/ tests/` (ignore line length if needed)

- [ ] T092 [P] Run mypy type checker: `mypy backend/` (fix type annotation issues)

- [ ] T093 [P] Run pytest with coverage: `pytest --cov=backend tests/` (ensure ≥80% coverage for core, ≥70% overall)

### Docker & Deployment

- [ ] T094 Create /docker/Dockerfile for containerized deployment: Python 3.11+ base image, install dependencies, expose port 8000

- [ ] T095 Create /docker/.dockerignore with exclusions: .env, __pycache__, .pytest_cache, .git

- [ ] T096 Create docker-compose.yml (optional) for local Neon/Qdrant simulation

### Final Validation

- [ ] T097 Run all tests: `pytest tests/ -v` (all must pass)

- [ ] T098 Manual smoke test: start server locally, create session, submit query, verify end-to-end flow works with real (or mocked) services

- [ ] T099 Verify no secrets in code: grep -r "OPENROUTER_API_KEY" backend/ --exclude-dir=.git (should find only placeholder in config.py)

- [ ] T100 Generate OpenAPI docs: visit http://localhost:8000/docs and verify all endpoints visible

---

## Task Summary

| Phase | Name | Task Count | Purpose |
|-------|------|-----------|---------|
| **1** | Setup | T001-T010 | Project initialization, dependencies |
| **2** | Foundational | T011-T027 | Database, models, external services, errors |
| **3** | US1: Full RAG | T028-T045 | Core query pipeline, main MVP |
| **4** | US2: Selected-Text | T046-T055 | Passage restriction mode |
| **5** | US3: Sessions | T056-T066 | Multi-turn conversation support |
| **6** | US4: Fallback | T067-T081 | Error handling, graceful degradation |
| **7** | Integration | T082-T085 | Cross-story validation |
| **8** | Polish | T086-T100 | Docs, code quality, deployment |
| **TOTAL** | | **100 tasks** | Complete implementation + testing |

---

## Execution Strategy: Recommended Order

### MVP (Minimum Viable Product) - Phase 1-3

Start here for quick demo:
1. Complete Phase 1: Setup (T001-T010)
2. Complete Phase 2: Foundational (T011-T027)
3. Complete Phase 3: User Story 1 (T028-T045)

**After Phase 3**: User can submit query → receive grounded answer with citations. Deployable MVP.

### Phase 2 Enhancement - Phase 4

Add selected-text mode (User Story 2, T046-T055)

### Phase 3 Enhancement - Phase 5

Add sessions & multi-turn (User Story 3, T056-T066)

### Production-Ready - Phase 6-8

Add fallback & error handling (User Story 4, T067-T081)
Integration testing (Phase 7, T082-T085)
Documentation & Polish (Phase 8, T086-T100)

---

## Parallelization Opportunities

### After Phase 2 (Foundational Complete):
- T029, T030, T031, T032 (Skills) can run in parallel
- T034, T035, T036 (Sub-agents) can run in parallel
- T042, T043, T044, T045 (Tests) can run in parallel

### After Phase 3 (Story 1 Complete):
- Phase 4 tasks (T046-T055) can run in parallel with Phase 5 setup (T056-T060)
- Story 2 and Story 3 can be developed concurrently

### Testing Throughout:
- Unit tests (T**/unit/) can run in parallel with implementation in same story
- Integration tests (T**/integration/) can run after story implementation complete

---

## Independent Test Criteria Per User Story

**User Story 1 (Full RAG Pipeline)**:
- ✅ POST /chat with valid query → 200 response with ChatResponse schema
- ✅ Answer contains content from retrieved_chunks
- ✅ Citations include section and url
- ✅ Metadata preserved (chunk_id, url, section)

**User Story 2 (Selected-Text Mode)**:
- ✅ POST /chat with selected_text parameter → only chunks from passage returned
- ✅ Answer grounded in selected passage OR explicit "Not found in selected passage"
- ✅ Retrieval scope visibly restricted

**User Story 3 (Sessions)**:
- ✅ POST /sessions → 201 with session_id
- ✅ GET /sessions/{id} → messages in order
- ✅ Multi-turn: Q1 → A1 → Q2 with context → A2 using context

**User Story 4 (Fallback)**:
- ✅ Off-topic query → fallback message (no hallucination)
- ✅ Qdrant down → graceful error
- ✅ LLM timeout → graceful error
- ✅ /health endpoint shows service statuses

---

## Success Criteria for Implementation

✅ **All 100 tasks completed**
✅ **Each task independently testable**
✅ **All tests passing (≥80% core coverage, ≥70% overall)**
✅ **All user stories deployable independently**
✅ **Zero hardcoded secrets**
✅ **No hallucinated answers (≥99% fallback accuracy)**
✅ **<5 sec response latency (p95 <10 sec)**
✅ **Production documentation complete**

---

## Next Steps

1. **Begin with Phase 1** (Setup): T001-T010
2. **Progress to Phase 2** (Foundational): T011-T027
3. **Implement User Story 1** (Phase 3): T028-T045 (MVP ready for demo)
4. **Iterate through remaining stories** (Phases 4-6) in priority order
5. **Integrate & test** (Phase 7): T082-T085
6. **Polish & deploy** (Phase 8): T086-T100

Each phase is a checkpoint with passing tests before proceeding.
