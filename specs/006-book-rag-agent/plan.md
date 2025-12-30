# Implementation Plan: BookRAGAgent — Multi-Agent Orchestration for Hallucination-Free RAG

**Branch**: `006-book-rag-agent` | **Date**: 2025-12-30 | **Spec**: [specs/006-book-rag-agent/spec.md](spec.md)
**Input**: Feature specification from `/specs/006-book-rag-agent/spec.md`

## Summary

BookRAGAgent is a multi-agent RAG backend system that orchestrates 5 specialized sub-agents (Retrieval, Answer, Guardrails, SelectionMode, Memory) with 6 modular skills to produce grounded, hallucination-free answers exclusively from book content. The system enforces zero-hallucination via multiple guardrails, supports selected-text-only queries, maintains session history, and integrates with OpenRouter LLM, Qdrant vector DB, and Neon PostgreSQL. All code adheres to security-first principles: secrets loaded from environment variables, no hardcoded keys, deterministic execution, and comprehensive logging for debugging.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, OpenAI Agents SDK, ChatKit SDK, qdrant-client, psycopg2-binary, openrouter (requests), pydantic, python-dotenv
**Storage**: Neon Serverless PostgreSQL (sessions), Qdrant Cloud (vectors)
**Testing**: pytest (unit + integration), mocks for external services
**Target Platform**: Linux server (Cloud-ready, Docker-compatible)
**Project Type**: Backend API (single service, modular agents)
**Performance Goals**: <5 sec response latency (p95 <10 sec), support concurrent users via session isolation
**Constraints**: No hallucinated answers (≥95% grounding rate), ≥99% fallback accuracy, metadata preserved for all chunks
**Scale/Scope**: Single book collection, multi-user sessions, up to 10,000+ chunks, 2-3 KLOC initial implementation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle 1: Security-First Foundation** ✅ PASS
- All secrets (OPENROUTER_API_KEY, QDRANT_API_KEY, DATABASE_URL) loaded from environment variables (.env)
- `.env` in `.gitignore`; `.env.example` with placeholders version-controlled
- Startup validation ensures all required env vars present; fails loudly if missing
- No API keys logged or echoed in responses/errors

**Principle 2: Zero-Hallucination Grounding** ✅ PASS
- All answers synthesized exclusively from retrieved chunks (FR-005)
- GuardrailsSubAgent vetos any answer containing inference or external knowledge (FR-006)
- Fallback message if no relevant chunks: "The answer cannot be found in the provided book content" (FR-008)
- Metadata preserved: source URL, section, chunk_id with every response (FR-003, FR-007)

**Principle 3: Developer-First Implementation** ✅ PASS
- All backend code in `/backend` directory (mandatory structure per constitution)
- Each logical unit in its own folder: agent/, rag/, storage/, models/, api/, services/
- Error messages are actionable with context (not generic "error occurred")
- Comprehensive logging for debugging without exposing secrets (FR-015)

**Principle 4: Reproducibility and Testability** ✅ PASS
- Database schema and API contracts version-controlled (data-model.md, contracts/)
- Unit tests for each skill (VectorSearchSkill, GroundedSynthesisSkill, etc.)
- Integration tests for agent orchestration with mocked external services
- Setup instructions in quickstart.md; deterministic environment initialization

**Principle 5: Deterministic Behavior** ✅ PASS
- No random seeds or non-deterministic behavior in agent execution
- Session persistence deterministic (SC-005): same user_id/session_id retrieves same context
- All external service calls tested with fixtures/mocks (Qdrant, OpenRouter, Neon)
- Error paths logged with full context for investigation

**Gate Result**: ✅ ALL PASS — No violations. Proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/006-book-rag-agent/
├── spec.md                          # User stories, requirements, success criteria
├── plan.md                          # This file (implementation architecture)
├── research.md                      # Phase 0: Research findings (to be created)
├── data-model.md                    # Phase 1: Entity definitions (to be created)
├── quickstart.md                    # Phase 1: Setup + local testing (to be created)
├── contracts/                       # Phase 1: API contracts (to be created)
│   ├── chat_endpoint.openapi.json
│   └── agent_messages.openapi.json
├── checklists/
│   └── requirements.md              # Quality validation (created)
└── tasks.md                         # Phase 2: Task breakdown (NOT created by /sp.plan)
```

### Source Code (Backend-Only, Per Constitution v2.0.0)

```text
backend/
├── agent/
│   ├── __init__.py
│   ├── agent.py                     # BookRAGAgent: main orchestration logic
│   ├── sub_agents.py                # RetrievalSubAgent, AnswerSubAgent, etc.
│   └── skills.py                    # VectorSearchSkill, GroundedSynthesisSkill, etc.
├── rag/
│   ├── __init__.py
│   ├── retrieval.py                 # VectorSearchSkill implementation (Qdrant queries)
│   ├── grounding.py                 # Hallucination detection & validation
│   └── embeddings.py                # Embedding model interface (Cohere)
├── storage/
│   ├── __init__.py
│   ├── sessions.py                  # Neon PostgreSQL session management
│   └── models.py                    # ORM models (User, Session, Message)
├── models/
│   ├── __init__.py
│   └── schemas.py                   # Pydantic models (Query, Response, Chunk, Citation)
├── api/
│   ├── __init__.py
│   └── routes.py                    # FastAPI endpoints (/chat, /sessions, /health)
├── services/
│   ├── __init__.py
│   ├── openrouter_service.py        # OpenRouter LLM client
│   └── text_selection.py            # Selected-text filtering logic
├── config.py                        # Environment variable loading, validation
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
├── .env.example                     # Template with placeholder values
└── pyproject.toml                   # Project metadata (Python 3.11+)

tests/
├── __init__.py
├── unit/
│   ├── test_vector_search.py        # VectorSearchSkill tests
│   ├── test_grounding.py            # Hallucination detection tests
│   ├── test_sessions.py             # Session persistence tests
│   └── test_text_selection.py       # Selected-text filtering tests
├── integration/
│   ├── test_agent_orchestration.py  # Full agent flow (mocked services)
│   └── test_chat_endpoint.py        # /chat endpoint tests (mocked Qdrant, LLM)
├── fixtures/
│   ├── mock_qdrant.py               # Mock Qdrant responses
│   ├── mock_openrouter.py           # Mock OpenRouter LLM responses
│   └── sample_chunks.py             # Sample book chunks for testing
└── conftest.py                      # pytest configuration

.env.example                         # Placeholder variables (version-controlled)
README.md                            # Setup and architecture overview
docker/
└── Dockerfile                       # Container image (optional, for deployment)
```

**Structure Decision**: Backend-only single service (Option 2 variant: backend only, no frontend). All code lives in `/backend` per Constitution v2.0.0 Mandatory Structure. No frontend code in this repository. Each logical unit (agent, rag, storage, api, services) in its own folder. Tests mirror source structure with unit, integration, and fixture subdirectories.

## Complexity Tracking

**No Constitution Violations** — All principles satisfied without deviations.

## Phase 0: Research & Resolution

**Objective**: Validate technical decisions, resolve any ambiguities, and produce research.md

### Research Tasks (No clarifications needed)

All technical decisions already determined by specification and constitution:

1. **Agent Orchestration Framework**
   - Decision: OpenAI Agents SDK + ChatKit SDK (per requirement input)
   - Rationale: Native support for multi-agent orchestration, sub-agent messaging, skill attachment
   - Alternatives considered: LangGraph (heavier), AutoGen (research focus, not production)
   - Status: ✅ CONFIRMED

2. **LLM Provider & Model Selection**
   - Decision: OpenRouter (not OpenAI API directly)
   - Rationale: Cost-effective, model flexibility, no vendor lock-in
   - Model: Claude 3.5 Sonnet or GPT-4o via OpenRouter (TBD during implementation, tunable via MODEL_NAME env var)
   - Status: ✅ CONFIRMED

3. **Vector Database**
   - Decision: Qdrant Cloud (free tier)
   - Rationale: Managed service, no ops burden, good Python client, metadata support
   - Embedding Model: Cohere embeddings (compatible, efficient)
   - Status: ✅ CONFIRMED

4. **Session Storage**
   - Decision: Neon Serverless PostgreSQL
   - Rationale: Serverless scaling, SQL for structured data, easy integration with Python
   - Schema: users, sessions, messages tables (defined in data-model.md)
   - Status: ✅ CONFIRMED

5. **Web Framework**
   - Decision: FastAPI (async, automatic OpenAPI docs, type safety via Pydantic)
   - Rationale: Modern Python async support, minimal boilerplate, excellent for APIs
   - Status: ✅ CONFIRMED

6. **Testing Strategy**
   - Decision: pytest with mocks for external services (Qdrant, OpenRouter, Neon)
   - Rationale: Deterministic tests, fast feedback, no external dependencies for unit/integration tests
   - Status: ✅ CONFIRMED

### Output
**File**: `research.md` (to be created with Phase 0 findings)

---

## Phase 1: Design & Contracts

**Objective**: Define data model, API contracts, deployment, and agent context updates

### Phase 1a: Data Model

**File**: `data-model.md` (to be created)

**Entities** (extracted from spec and user stories):

1. **User** (optional, if multi-user authentication handled)
   - user_id: string (UUID)
   - created_at: timestamp

2. **Session**
   - session_id: string (UUID)
   - user_id: string (foreign key to User)
   - created_at: timestamp
   - updated_at: timestamp
   - metadata: JSON (optional client data)

3. **ChatMessage**
   - message_id: string (UUID)
   - session_id: string (foreign key to Session)
   - role: enum ("user" | "assistant")
   - content: text
   - metadata: JSON (chunks_used, tokens, latency, etc.)
   - created_at: timestamp

4. **RetrievedChunk** (in-memory during request, also logged to messages)
   - chunk_id: string
   - text: string
   - metadata: JSON (url, section, position, embedding_similarity)

5. **APIRequest/Response** (Pydantic models)
   - ChatRequest: question, session_id, selected_text (optional)
   - ChatResponse: answer, citations, retrieved_chunks

### Phase 1b: API Contracts

**File**: `contracts/chat_endpoint.openapi.json` (to be created)

**Endpoints**:

1. **POST /chat**
   - Request: { "question": string, "session_id": string, "selected_text": string (optional) }
   - Response: { "answer": string, "citations": [ { "section": string, "url": string } ], "retrieved_chunks": [ { "text": string, "metadata": {...} } ] }
   - Status Codes: 200 (success), 400 (invalid input), 500 (service error)

2. **POST /sessions** (create new session)
   - Response: { "session_id": string, "created_at": timestamp }

3. **GET /sessions/{session_id}** (retrieve session with history)
   - Response: { "session_id": string, "messages": [ { "role": string, "content": string, "created_at": timestamp } ] }

4. **GET /health** (health check)
   - Response: { "status": "healthy", "services": { "qdrant": "ok", "database": "ok", "openrouter": "ok" } }

### Phase 1c: Quickstart

**File**: `quickstart.md` (to be created)

**Contents**:
- Prerequisites (Python 3.11+, pip/uv, git)
- Environment setup (.env configuration)
- Installation (pip install -r requirements.txt)
- Running the server (uvicorn backend.main:app --reload)
- Testing with curl examples
- Running test suite (pytest)

### Phase 1d: Agent Context Update

**Objective**: Register BookRAGAgent architecture in agent context file

**Command**: (to be run after plan approval)
```bash
.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude
```

**Contents to add**:
- BookRAGAgent orchestration architecture
- Sub-agents: RetrievalSubAgent, AnswerSubAgent, GuardrailsSubAgent, SelectionModeSubAgent, MemorySubAgent
- Skills: VectorSearchSkill, SelectedTextOverrideSkill, GroundedSynthesisSkill, RetrievalValidationSkill, AntiHallucinationSkill, SessionPersistenceSkill
- Execution flow diagram
- Environment variables and secrets management

---

## Phase 2: Task Breakdown (Not created by /sp.plan)

**Next Command**: `/sp.tasks`

This will produce `tasks.md` with implementation tasks organized by:
- Phase 1: Setup (project structure, dependencies)
- Phase 2: Foundations (base classes, database setup, config loading)
- Phase 3: User Story 1 (Full RAG Pipeline)
- Phase 4: User Story 2 (Selected-Text Mode)
- Phase 5: User Story 3 (Sessions & Multi-Turn)
- Phase 6: User Story 4 (Fallback & Guardrails)
- Phase 7: Testing & Validation
- Phase 8: Documentation & Deployment

Each task will be:
- Independently testable where possible
- Include specific file paths and code examples
- Reference the associated user story and success criteria
- Marked as unit (single-developer) or integration (multiple files)

---

## Key Design Decisions

### 1. Multi-Agent Orchestration Pattern
**Decision**: Separate sub-agents for each responsibility (Retrieval, Answer, Guardrails, SelectionMode, Memory)
**Rationale**: Modular, testable, role-specific error handling, reusable skills
**Implications**: More code organization, clearer responsibilities, easier to extend

### 2. Guardrails-First Approach
**Decision**: GuardrailsSubAgent runs AFTER AnswerSubAgent, has veto authority
**Rationale**: "Fail-safe" design; better to return "not found" than a hallucinated answer
**Implications**: Two-pass synthesis (attempt + validate); latency increase negligible (~100ms)

### 3. Selected-Text as Retrieval Override (Not Post-Filter)
**Decision**: SelectionModeSubAgent overrides retrieval scope before VectorSearchSkill executes
**Rationale**: Efficient (don't retrieve all then filter); more trustworthy (visibly respects user constraint)
**Implications**: Requires passage_id metadata in chunks; additional retrieval mode parameter

### 4. Session Storage Separate from Retrieval Knowledge Source
**Decision**: MemorySubAgent reads sessions but sessions NEVER used as retrieval context
**Rationale**: Prevents session history (user's prior wrong answers) from contaminating knowledge base
**Implications**: More complex prompt engineering (disambiguate via context without mentioning it); cleaner RAG

### 5. Environment Variables for All Secrets
**Decision**: OPENROUTER_API_KEY, QDRANT_API_KEY, DATABASE_URL all from .env
**Rationale**: Zero hardcoded secrets, portable deployment, security compliance
**Implications**: Startup validation required; clear error messages for missing vars

---

## Success Criteria for Implementation Planning

✅ **Constitution Check**: All 5 principles validated, no violations
✅ **Technical Context**: All fields filled (language, dependencies, storage, testing, platform, performance, constraints, scale)
✅ **Project Structure**: Clear folder organization matching constitution requirements
✅ **Phases Defined**: Phase 0 (research), Phase 1 (design), Phase 2 (tasks) outlined
✅ **Key Decisions**: 5 major design decisions documented with rationale
✅ **Ready for Phase 0**: No unresolved clarifications; proceed to research.md generation

---

**Next Steps**:
1. Review this plan for approval
2. Run `/sp.tasks` to generate task breakdown
3. Begin implementation following phase-based task sequence
