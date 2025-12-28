# Implementation Tasks: RAG Agent with OpenAI Integration

**Feature**: `005-rag-agent-openai` | **Branch**: `005-rag-agent-openai` | **Target**: Hackathon Demo
**Start**: 2025-12-28 | **Scope**: Single `agent.py` module with OpenAI Agents integration + Cohere retrieval

## Summary

16 focused tasks to implement RAG agent with OpenAI integration. Organized by user story (4 P1 stories + 1 P2 story). MVP scope: complete Phase 1-3 tasks for agent initialization, retrieval, and Q&A functionality. Phase 4 (response synthesis) is P2 enhancement.

## User Stories & Priority

- **US1 (P1)**: Ask Textbook Questions - Agent answers queries grounded in textbook content
- **US2 (P1)**: Agent Initialization & Health Check - Agent starts successfully with Qdrant/Cohere
- **US3 (P1)**: Retrieve Context from Textbook - Queries return top-k chunks with scores
- **US4 (P2)**: Generate Natural Language Responses - Synthesize conversational answers

---

## Phase 1: Setup & Infrastructure

Shared setup for all user stories - **MUST COMPLETE FIRST**

- [ ] T001 Verify existing environment: Check .env has OPENAI_API_KEY, COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME=rag_embedding
- [ ] T002 Review existing backend structure: Understand main.py, retrieve.py, .env configuration, imports
- [ ] T003 Create agent.py skeleton in backend/ with imports (openai, cohere, qdrant_client, dotenv, logging, json, sys)
- [ ] T004 Set up logging in agent.py: Configure logging with file + console output to agent_YYYYMMDD_HHMMSS.log
- [ ] T005 Load environment variables in agent.py: Parse .env and validate all required API keys present

## Phase 2: Agent Foundation (Foundational for all user stories)

Blocking prerequisites - **MUST COMPLETE BEFORE USER STORIES**

- [ ] T006 [P] Implement query validation function: validate_query(query_text) checks 3-5000 char range, returns True/False
- [ ] T007 [P] Implement Cohere query encoder: encode_query(query_text) → 1024-dim embedding using input_type="search_query"
- [ ] T008 [P] Implement Qdrant search function: search_qdrant(embedding, k=5) → List[dict] with id, score, payload
- [ ] T009 [P] Implement result formatter: format_retrieved_chunks(search_results) → List[dict] with rank, similarity_score, content, source_url, chunk_position, created_at, chunk_size
- [ ] T010 [P] Implement error handler: Handle Cohere rate limits (exponential backoff, max 5 retries), Qdrant connection errors, timeouts
- [ ] T011 Implement health check: agent_health_check() returns dict with {status: "ready", message, metadata} including API availability

## Phase 3: User Story 1 - Ask Textbook Questions (P1)

Independent testing of question-answering capability

- [ ] T012 [US1] Create main query handler: run_query(query_text, k=5) orchestrates encode → search → format → return response JSON
- [ ] T013 [US1] Implement response wrapper: Build QueryResponse dict with {query, response, sources, confidence, execution_time_ms, status}
- [ ] T014 [US1] Add CLI interface for single query: python agent.py "question here" outputs formatted JSON response
- [ ] T015 [US1] Run manual test: Execute agent.py with 5+ test queries covering all 8 textbook modules (fundamentals, navigation, kinematics, ROS, perception, ML, hardware, physics)
- [ ] T016 [US1] Validate response quality: Check (1) 90%+ queries return relevant results, (2) similarity scores in [0,1], (3) sources cited correctly, (4) execution time < 5s per query

## Phase 4: User Story 2 - Agent Initialization & Health Check (P1)

Independent verification of agent readiness

- [ ] T017 [US2] Create agent initialization function: agent_init() calls health_check(), confirms Qdrant connection, validates Cohere API
- [ ] T018 [US2] Implement Qdrant connection test: Verify collection "rag_embedding" exists and is accessible (verify vector dimensionality = 1024)
- [ ] T019 [US2] Implement Cohere API test: Encode test query, verify response has 1024-dim embedding
- [ ] T020 [US2] Create startup entrypoint: if __name__ == "__main__": agent_init() with success/failure messages

## Phase 5: User Story 3 - Retrieve Context from Textbook (P1)

Independent testing of retrieval mechanism

- [ ] T021 [US3] Implement batch query handler: run_batch_queries(queries_list, k=5) processes multiple queries, returns aggregated results
- [ ] T022 [US3] Add batch CLI interface: python agent.py --batch test_queries.json --k 5 --log batch_results.log
- [ ] T023 [US3] Implement batch logging: Write all batch results to JSON log file with timestamps, including statistics (avg/min/max similarity_score, successful_queries, error_count)
- [ ] T024 [US3] Run batch validation: Execute all 12 test queries from test_queries.json, verify 90%+ success rate
- [ ] T025 [US3] Validate retrieval metrics: Confirm (1) top-5 chunks returned per query, (2) similarity scores sorted descending, (3) metadata complete (URLs, positions, timestamps)

## Phase 6: User Story 4 - Generate Natural Language Responses (P2)

Natural language synthesis - **OPTIONAL for MVP**

- [ ] T026 [US4] [P2] Create OpenAI Agent with retrieval tool: Initialize OpenAI Agents client with retrieve_from_textbook tool
- [ ] T027 [US4] [P2] Implement response synthesis prompt: Design system prompt for agent to synthesize responses from retrieved chunks with citations
- [ ] T028 [US4] [P2] Integrate OpenAI Agent into run_query: Modify run_query to use agent.process() instead of raw response wrapper
- [ ] T029 [US4] [P2] Test response quality: Run 5+ queries, verify responses are (1) coherent and grammatical, (2) cite sources explicitly, (3) address user question directly
- [ ] T030 [US4] [P2] Compare agent vs. retrieval: Document differences between raw retrieval (Phase 3) vs. agent synthesis (Phase 4)

## Phase 7: Polish & Cross-Cutting Concerns

Final validation and documentation

- [ ] T031 Update backend/README.md with Agent section: Add quick start examples (single query, batch test), usage instructions, troubleshooting
- [ ] T032 Add docstrings to agent.py: Document all functions (purpose, args, return, errors), add type hints
- [ ] T033 Verify single-file constraint: Confirm all code in agent.py only (no separate files, no imports from custom modules except retrieve.py if shared)
- [ ] T034 End-to-end validation: Run full agent.py with all 12 test queries, measure total time, verify all success criteria met
- [ ] T035 Prepare for hackathon demo: Create demo script that runs agent with 3-5 highlight queries, formats output for judges

---

## Dependency Graph & Execution Strategy

### Strict Sequence (blocking):

1. **Phase 1** (T001-T005): Setup & .env (prerequisite for all)
2. **Phase 2** (T006-T011): Agent foundation (prerequisite for user stories)
3. **Phases 3-6**: User stories (can run in parallel after Phase 2)
4. **Phase 7** (T031-T035): Polish (final)

### Parallelizable within phases:

- **Phase 2**: T006-T010 can run in parallel (different functions, no inter-task dependencies)
- **Phase 3-6**: Each user story (US1-US4) can run in parallel after Phase 2 complete
- **Phase 7**: T031-T034 can run in parallel, T035 depends on T034

### MVP Scope (Minimum Viable Product):

- ✅ **Complete**: Phase 1-5 (Setup + Foundation + US1/US2/US3)
- ✅ **Sufficient for hackathon**: Judges can run agent.py and see retrieval results
- ✅ **Optional enhancement**: Phase 6 (US4 - OpenAI Agent response synthesis)

---

## Independent Test Criteria

### US1: Ask Textbook Questions (P1)

**Independent Test** (T012-T016):
1. Execute agent.py with 5+ diverse queries covering all 8 modules
2. Verify: (1) 90%+ queries return relevant results, (2) responses cite textbook content, (3) execution time < 5s per query
4. **Deliverable**: agent_validation_results.log with query → response mappings

### US2: Agent Initialization & Health Check (P1)

**Independent Test** (T017-T020):
1. Execute agent.py startup
2. Verify: (1) health check passes, (2) Qdrant connection confirmed, (3) Cohere API accessible, (4) startup logs show "Agent ready"
3. **Deliverable**: startup log with all checks passing

### US3: Retrieve Context from Textbook (P1)

**Independent Test** (T021-T025):
1. Run batch test with all 12 test_queries.json
2. Verify: (1) 90%+ success rate, (2) top-5 chunks returned per query, (3) similarity scores in [0,1] and sorted descending, (4) metadata complete
3. **Deliverable**: batch_results.log with statistics

### US4: Generate Natural Language Responses (P2)

**Independent Test** (T026-T030):
1. Run 5+ queries through OpenAI Agent
2. Verify: (1) responses are coherent and grammatical, (2) sources explicitly cited, (3) directly addresses user question
3. **Deliverable**: agent_synthesis_comparison.json comparing raw retrieval vs. agent synthesis

---

## Success Criteria Mapping

| SC | Requirement | Implementation Task |
|----|-------------|-------------------|
| SC-001 | Agent initializes and confirms Qdrant connection | T017 (agent_init) |
| SC-002 | Retrieves top-k chunks for 100% of valid queries | T012 (run_query) |
| SC-003 | Similarity scores in [0,1], sorted descending | T009 (format_chunks) |
| SC-004 | 5+ queries covering all 8 textbook modules | T015 (manual test) |
| SC-005 | Each response incorporates context with citations | T013 (response wrapper) |
| SC-006 | < 5 second response time (95%) | T015 (validate metrics) |
| SC-007 | Error handling with user-friendly messages | T010 (error handler) |
| SC-008 | Timestamped logs for audit trail | T004 (logging setup) |
| SC-009 | Deployable locally with .env credentials | T001-T002 (env setup) |
| SC-010 | Complete in single agent.py file | T033 (single-file constraint) |

---

## File Summary

| File | Status | Deliverable |
|------|--------|--------------|
| backend/agent.py | TO BUILD | Main implementation (all 35 tasks) |
| backend/.env | READY | Configuration with all keys |
| backend/test_queries.json | READY | 12 test queries (from Spec 002) |
| backend/README.md | TO UPDATE | Agent section with quick start |
| agent_YYYYMMDD_HHMMSS.log | GENERATED | Single query execution logs |
| batch_results.log | GENERATED | Batch test results |

---

## Implementation Notes

**Architecture**: Single `backend/agent.py` with 8 core functions:
- `validate_query()` - Input validation
- `encode_query()` - Cohere embeddings (1024-dim)
- `search_qdrant()` - Vector similarity search
- `format_retrieved_chunks()` - Result formatting
- `agent_health_check()` - System diagnostics
- `run_query()` - Single query orchestration (US1-US3)
- `run_batch_queries()` - Batch processing (US3)
- `agent_init()` - Startup sequence (US2)

Plus optional OpenAI Agent integration for US4.

**No new dependencies**: Reuses Spec 001-002 (cohere, qdrant-client, python-dotenv) + adds openai SDK only

**Estimated scope**: ~400-500 lines of well-documented Python code

**Testing approach**: Manual validation via query execution + batch test suite (no pytest framework for MVP)

---

## Next Steps

1. **BackendEngineer**: Begin Phase 1 setup (T001-T005), then Phase 2 foundation (T006-T011)
2. **Parallel Development**: After Phase 2, work on US1-US3 in parallel (Phases 3-5)
3. **Optional Enhancement**: US4 response synthesis if time permits (Phase 6)
4. **Final Push**: Phase 7 polish + demo preparation
5. **Hackathon Demo**: Execute `python agent.py --batch test_queries.json` for judges

**MVP Definition**: Phases 1-5 complete = full RAG agent with retrieval working. US4 (response synthesis) is nice-to-have bonus.

---

**Branch**: `005-rag-agent-openai` ready for implementation. All 35 tasks are concrete, testable, and ordered for efficient execution.
