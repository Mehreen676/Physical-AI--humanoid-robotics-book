---
id: 003
title: BookRAGAgent task breakdown complete
stage: tasks
date: 2025-12-30
surface: agent
model: claude-haiku-4-5-20251001
feature: 006-book-rag-agent
branch: 006-book-rag-agent
user: mehreen@example.com
command: /sp.tasks
labels: ["task-breakdown", "implementation", "100-tasks", "phased-delivery"]
links:
  spec: specs/006-book-rag-agent/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-book-rag-agent/tasks.md
tests:
  - 100 tasks generated with strict format compliance
  - All tasks have [ID], [P?], [Story?] labels correctly applied
  - Each task includes specific file paths
  - Tasks organized by 8 phases (Setup, Foundational, 4 User Stories, Integration, Polish)
  - Phase-by-phase dependencies respected
  - Parallel opportunities identified per phase
  - Independent test criteria defined for each user story
  - MVP scope identified (Phases 1-3)
---

## Prompt

```
$ARGUMENTS
[Standard task generation outline from SpecKit Plus]
```

## Response snapshot

**✅ TASK BREAKDOWN COMPLETE: BookRAGAgent (100 tasks across 8 phases)**

**Deliverable**: `specs/006-book-rag-agent/tasks.md` (499 lines, 26KB)

**Task Count & Distribution**:
- Phase 1 (Setup): 10 tasks (T001-T010)
- Phase 2 (Foundational): 17 tasks (T011-T027)
- Phase 3 (User Story 1): 18 tasks (T028-T045)
- Phase 4 (User Story 2): 10 tasks (T046-T055)
- Phase 5 (User Story 3): 11 tasks (T056-T066)
- Phase 6 (User Story 4): 15 tasks (T067-T081)
- Phase 7 (Integration): 4 tasks (T082-T085)
- Phase 8 (Polish): 15 tasks (T086-T100)
- **TOTAL**: 100 tasks

**Format Validation** ✅
- All 100 tasks follow strict checklist format: `- [ ] [ID] [P?] [Story?] Description with filepath`
- All tasks have sequential IDs (T001-T100)
- Story labels correctly applied only to user story phases ([US1], [US2], [US3], [US4])
- Parallelizable tasks marked with [P] flag (18 tasks)
- All tasks include specific file paths (absolute from /backend or /tests)

**Phase-by-Phase Breakdown**:

**Phase 1: Setup (T001-T010)**
- Project structure creation
- Dependencies & requirements.txt
- FastAPI app initialization
- Environment variable configuration & validation
- Test framework setup
- Checkpoint: Basic FastAPI server runs, env validation works

**Phase 2: Foundational (T011-T027)** ⚠️ BLOCKING PHASE
- Pydantic models & schemas (5 tasks)
- SQLAlchemy ORM models & database setup (4 tasks)
- SessionManager class (3 tasks)
- External service integration: OpenRouter, Embeddings, Qdrant (4 tasks)
- Logging & error handling (3 tasks)
- Input validation (3 tasks)
- **Checkpoint**: All external services mocked & tested, database ready, errors handled, 17 tests passing

**Phase 3: User Story 1 - Full RAG Pipeline (T028-T045)** 🎯 MVP
- VectorSearchSkill, GroundedSynthesisSkill, AntiHallucinationSkill (3 tasks)
- RetrievalSubAgent, AnswerSubAgent, GuardrailsSubAgent (3 tasks)
- BookRAGAgent orchestration (2 tasks)
- POST /chat endpoint (2 tasks)
- Integration & unit tests (6 tasks)
- **Checkpoint**: User can submit query → receive grounded answer with citations. MVP deployable.

**Phase 4: User Story 2 - Selected-Text Mode (T046-T055)**
- SelectedTextOverrideSkill (1 task)
- VectorSearchSkill enhancement for filtering (1 task)
- SelectionModeSubAgent (1 task)
- Agent flow modification (2 tasks)
- API endpoint enhancement (1 task)
- Tests (3 tasks)
- **Checkpoint**: Selected-text mode works, Stories 1-2 passing

**Phase 5: User Story 3 - Sessions & Multi-Turn (T056-T066)**
- SessionPersistenceSkill (1 task)
- MemorySubAgent (2 tasks)
- Agent flow for context retrieval (2 tasks)
- POST /sessions and GET /sessions/{id} endpoints (2 tasks)
- Tests (4 tasks)
- **Checkpoint**: Multi-turn conversation working, Stories 1-3 passing

**Phase 6: User Story 4 - Fallback & Errors (T067-T081)**
- Error handling enhancements (3 tasks)
- Service failure handling (3 tasks)
- Guardrails validation enhancements (2 tasks)
- API response handling (2 tasks)
- GET /health endpoint (1 task)
- Tests (4 tasks)
- **Checkpoint**: Graceful error handling, zero hallucinations, Stories 1-4 passing

**Phase 7: Integration & Cross-Story Validation (T082-T085)**
- Full workflow tests (1 task)
- Concurrency tests (1 task)
- Metadata preservation tests (1 task)
- Schema validation tests (1 task)
- **Checkpoint**: All stories work together, no regressions

**Phase 8: Documentation & Polish (T086-T100)**
- Architecture documentation (3 tasks)
- Code quality (4 tasks)
- Docker & deployment (3 tasks)
- Final validation & manual testing (5 tasks)
- **Checkpoint**: Production-ready, fully documented, deployed

**User Story Mapping**:

**User Story 1 (Full RAG Pipeline)** - 18 tasks
- Skills: VectorSearchSkill, GroundedSynthesisSkill, AntiHallucinationSkill, RetrievalValidationSkill
- Sub-agents: RetrievalSubAgent, AnswerSubAgent, GuardrailsSubAgent
- Agent: BookRAGAgent.execute() with orchestration flow
- Endpoint: POST /chat
- Tests: 6 integration/unit tests
- MVP deliverable ✅

**User Story 2 (Selected-Text Mode)** - 10 tasks
- Skills: SelectedTextOverrideSkill
- Sub-agents: SelectionModeSubAgent (enhancement to RetrievalSubAgent)
- Modification: VectorSearchSkill retrieval scope filtering
- Endpoint: /chat with selected_text parameter
- Tests: 3 tests
- Builds on Story 1 ✅

**User Story 3 (Multi-Turn Sessions)** - 11 tasks
- Skills: SessionPersistenceSkill
- Sub-agents: MemorySubAgent (enhancement to AnswerSubAgent)
- Endpoints: POST /sessions, GET /sessions/{id}
- Modification: Agent flow for context retrieval
- Tests: 4 tests
- Builds on Story 1 ✅

**User Story 4 (Fallback & Errors)** - 15 tasks
- Enhancements to existing skills (error handling)
- New endpoint: GET /health
- Service failure graceful handling
- Hallucination veto enforcement
- Tests: 4 tests
- Builds on all stories ✅

**Parallelization Opportunities**:

**After Phase 2 Complete** (Foundational ready):
- Skills T029, T030, T031, T032 can run in parallel
- Sub-agents T034, T035, T036 can run in parallel
- Tests T042-T045 can run in parallel

**After Phase 3 Complete** (Story 1 done):
- Phase 4 (Story 2) T046-T055 can run in parallel
- Phase 5 (Story 3) setup T056-T060 can run in parallel
- Different stories independent (can hire multiple developers)

**Throughout**:
- All [P] marked tasks can run in parallel
- Unit tests can run during story implementation
- Integration tests can run after story implementation

**MVP Scope** (Deliver First):
- Phase 1: Setup ✅
- Phase 2: Foundational ✅
- Phase 3: User Story 1 ✅
- After these 3 phases: MVP complete, system answering questions from book

**Incremental Delivery**:
- MVP (Phases 1-3): Core RAG pipeline
- Phase 4 +: Add selected-text mode
- Phase 5 +: Add multi-turn sessions
- Phase 6 +: Robust error handling
- Phase 7-8: Integration & production-ready

**Independent Test Criteria** ✅

**Story 1 (Full RAG)**:
- ✓ POST /chat with valid query → 200 + ChatResponse schema
- ✓ Answer contains content from retrieved_chunks
- ✓ Citations include section + url
- ✓ Metadata preserved in response

**Story 2 (Selected-Text)**:
- ✓ /chat with selected_text parameter → only chunks from passage
- ✓ Answer grounded in passage OR explicit "Not found"
- ✓ Retrieval scope visibly restricted

**Story 3 (Sessions)**:
- ✓ POST /sessions → 201 with session_id
- ✓ GET /sessions/{id} → messages in order
- ✓ Multi-turn: Q1→A1→Q2(with context)→A2

**Story 4 (Fallback)**:
- ✓ Off-topic query → fallback message (no hallucination)
- ✓ Qdrant down → graceful error
- ✓ LLM timeout → graceful error
- ✓ /health shows service statuses

**Success Metrics** ✅
- All 100 tasks completed
- Each task independently testable
- ≥80% core coverage, ≥70% overall
- All user stories independently deployable
- Zero hardcoded secrets
- ≥99% fallback accuracy
- <5 sec response latency
- Full documentation

## Outcome

- ✅ Impact: Complete task breakdown ready for immediate implementation; 100 specific, actionable tasks with exact file paths
- 🧪 Tests: Format validation PASS (all 100 tasks follow checklist format); phase dependencies satisfied; parallelization identified; independent test criteria defined
- 📁 Files: tasks.md (499 lines, 26KB) with full task list, phase breakdown, execution strategy
- 🔁 Next steps: Begin Phase 1 (T001-T010); proceed through phases sequentially; MVP ready after Phase 3
- 🧠 Reflection: Task breakdown captures complete implementation journey from setup through production-ready deployment. Each task is scoped for single developer or pair. Phases enable progressive delivery with working MVP at end of Phase 3. All 4 user stories independently testable and deployable.

## Evaluation notes (flywheel)

- Failure modes observed: None; all 100 tasks generated with correct format and file paths
- Graders run and results (PASS/FAIL): Format validation PASS; phase organization PASS; task count per phase correct; story mapping complete
- Prompt variant (if applicable): Standard task generation workflow (load spec/plan, extract stories, map to tasks, organize by phase)
- Next experiment: Begin Phase 1 implementation with T001-T010; expect 4-6 hours to complete setup phase
