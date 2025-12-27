# Implementation Tasks: RAG Retrieval Testing

**Feature**: `002-rag-retrieval-testing` | **Branch**: `002-rag-retrieval-testing` | **Target**: Hackathon Demo
**Start**: 2025-12-28 | **Scope**: Single `retrieve.py` module with 6 core functions + batch testing

## Summary

10 focused tasks to implement retrieval testing module for validating RAG embedding pipeline. Organized by user story priority (4 P1 stories, 1 P2 story). MVP scope: complete all Phase 1-2 tasks for single-query and batch testing functionality.

## User Stories & Priority

- **US1 (P1)**: Similarity Search from Stored Embeddings
- **US2 (P1)**: Book-Specific Content Accuracy
- **US3 (P2)**: Metadata and Source Attribution
- **US4 (P1)**: Comprehensive Multi-Module Query Testing

---

## Phase 1: Setup & Infrastructure

Shared setup for all user stories - **MUST COMPLETE FIRST**

- [x] T001 Verify Spec 001 completion: Check backend/.env configured, Qdrant collection populated, Cohere API accessible
- [x] T002 Review existing backend structure: Understand main.py, .env configuration, imports (cohere, qdrant-client)

## Phase 2: Core Retrieval Functions (Foundational for all stories)

Blocking prerequisites - **MUST COMPLETE BEFORE USER STORIES**

- [x] T003 [P] Implement encode_query(query_text: str) -> List[float] in backend/retrieve.py
  - Use cohere.ClientV2 with reused COHERE_API_KEY from .env
  - Validate input: 3-5000 chars; raise ValueError if invalid
  - Add exponential backoff retry for rate limits (max 5 retries)
  - Return exactly 1024-dimensional vector
  - Accept: Returns List[float] with len=1024; values in [-1, 1] range

- [x] T004 [P] Implement search_qdrant(embedding: List[float], k: int = 5, timeout: int = 10) -> List[dict] in backend/retrieve.py
  - Use QdrantClient(QDRANT_URL, QDRANT_API_KEY) from .env
  - Query existing "rag_embedding" collection
  - Return top-k results sorted by similarity_score descending
  - Handle ConnectionError and TimeoutError with logging
  - Accept: Returns list of dicts with id, score, payload fields

- [x] T005 [P] Implement retrieve_chunks(query_text: str, k: int = 5) -> QueryResponse in backend/retrieve.py
  - Orchestrate: encode_query() → search_qdrant() → format as QueryResponse
  - Build QueryResponse with all fields: query, embedding_dimension, timestamp, k, results, result_count, execution_time_ms, status
  - Track execution time from start to finish
  - Include ISO-8601 timestamp
  - Accept: Returns QueryResponse with execution_time_ms < 3000ms; all fields populated

- [x] T006 [P] Implement validate_results(results: List[RetrievedChunk]) -> dict in backend/retrieve.py
  - Validate similarity_score in [0, 1] range and sorted descending
  - Verify content exactly matches stored chunks (no corruption)
  - Check metadata complete: source_url (valid HTTP(S)), chunk_position (int), created_at (ISO-8601)
  - Check JSON serializable (no custom objects)
  - Return dict: {is_valid: bool, checks_passed: int, checks_failed: int, issues: List[str]}
  - Accept: All validation checks pass for valid results; identifies issues correctly

- [x] T007 [P] Format results as QueryResponse JSON objects in backend/retrieve.py
  - Convert Qdrant search results to RetrievedChunk objects (rank, similarity_score, content, source_url, chunk_position, created_at)
  - Build QueryResponse with results array, metadata, timestamps
  - Ensure JSON-serializable (test with json.dumps())
  - Accept: Valid JSON output; all required fields present; no custom object references

## Phase 3: Single Query Testing (US1, US2, US3 - P1 foundation)

Independent testing of single queries for judges

- [x] T008 [US1] Implement run_single_query(query_text: str, k: int = 5, log_file: str = None) -> None in backend/retrieve.py
  - Call retrieve_chunks() to get QueryResponse
  - Call validate_results() to validate
  - Print formatted JSON to console (use json.dumps with indent=2)
  - Log to file if log_file provided: append with timestamp
  - Include execution_time_ms and validation metrics in output
  - Accept: JSON printed; matches QueryResponse schema; logged if requested

## Phase 4: Batch Testing (US4 - P1 comprehensive validation)

Multi-query testing across all modules for comprehensive judge evaluation

- [x] T009 [US4] Create test query suite (10+ diverse queries) in backend/test_queries.json
  - Design queries covering all major textbook modules/topics
  - Include edge cases: broad queries, narrow queries, ambiguous queries
  - Format: List[{"query": "...", "expected_modules": [...], "description": "..."}]
  - Minimum 10 queries; document expected topic coverage
  - Accept: 10+ queries in JSON; covers all identified modules; documented

- [x] T010 [US4] Implement run_batch_test(queries: List[str], k: int = 5, log_file: str = None) -> TestResultLog in backend/retrieve.py
  - Iterate through queries list, execute retrieve_chunks() for each
  - Call validate_results() for each result
  - Aggregate into TestResultLog: test_id (UUID), test_type ("batch"), timestamp, results array
  - Calculate statistics: avg/min/max similarity_score, avg_execution_time_ms, successful_queries, empty_results_count, error_count
  - Log complete results to file (log_file parameter) with timestamp
  - Print summary to console: test_id, total queries, successful_queries, avg_score, avg_time
  - Accept: Processes all 10+ queries; aggregates statistics; logs results with timestamps

## Phase 5: Documentation & Validation

Cross-cutting concerns and final validation

- [x] T011 Update backend/README.md with "Retrieval Testing" section
  - Add quick start: "python backend/retrieve.py" usage with examples
  - Document run_single_query() and run_batch_test() with parameters
  - Include example output (sample JSON response)
  - Document log file locations and format
  - Add troubleshooting: what to do if Qdrant unavailable, rate limits hit, etc.
  - Accept: Clear instructions for judges to run independently; examples provided

- [x] T012 End-to-end validation: Run full test suite and verify success criteria
  - Execute batch_test() with all 10+ queries from test_queries.json
  - Verify SC-001: Similarity search returning top-k chunks ✓
  - Verify SC-002: ≥90% of queries return relevant results (judge review)
  - Verify SC-003: Content accuracy 100% (spot-check 3+ results)
  - Verify SC-004: Book-specific content terminology (judge review)
  - Verify SC-005: 100% metadata inclusion (all results)
  - Verify SC-006: 10+ queries covering all modules (checklist)
  - Verify SC-007: All results logged with timestamps
  - Verify SC-008: Valid JSON formatting (json.dumps successful)
  - Verify SC-009: Edge cases handled (empty results, errors logged)
  - Verify SC-010: Response time <3s 95% of time (measure batch_test)
  - Document test run with date/time for hackathon demo
  - Accept: All 10 success criteria verified; test results logged; ready for judge presentation

---

## Dependency Graph & Execution Strategy

### Strict Sequence (blocking):
1. **T001-T002**: Setup/infrastructure checks (prerequisite for all)
2. **T003-T007**: Core functions (prerequisite for testing)
3. **T008-T010**: Testing (uses core functions)
4. **T011-T012**: Documentation & validation (final)

### Parallelizable within phases:
- **Phase 2**: T003-T007 can run in parallel (different functions, no inter-task dependencies)
- **Phase 3-4**: T008-T010 can run in parallel after Phase 2 complete
- **Phase 5**: T011-T012 can start after T010 complete

### MVP Scope (Minimum Viable Product):
- ✅ **Complete**: T001-T010 (all core functions + batch testing)
- ✅ **Sufficient for hackathon**: Judges can run retrieve.py and see results
- ✅ Optional enhancement: T011-T012 (docs + validation)

---

## Success Criteria Mapping

| SC | Requirement | Implementation Task |
|----|-------------|-------------------|
| SC-001 | Similarity search returns top-k | T004 (search_qdrant), T005 (retrieve_chunks) |
| SC-002 | ≥90% queries relevant results | T010 (aggregate metrics), T012 (validate) |
| SC-003 | 100% content accuracy | T006 (validate_results), T012 (spot-check) |
| SC-004 | Book-specific terminology | T009 (query design), T012 (judge review) |
| SC-005 | 100% metadata inclusion | T006 (validate), T007 (format), T010 (check) |
| SC-006 | 10+ module-covering queries | T009 (create query suite) |
| SC-007 | Results logged with timestamps | T008 (single), T010 (batch), T012 (verify) |
| SC-008 | Valid JSON formatting | T007 (format), T006 (validate), T012 (verify) |
| SC-009 | Edge cases handled | T006 (validate), T012 (test) |
| SC-010 | <3s response 95% of time | T005 (timing), T010 (aggregate), T012 (measure) |

---

## Implementation Notes

**Architecture**: Single `backend/retrieve.py` with 6 core functions + helpers
- `encode_query()` - Convert query to embedding
- `search_qdrant()` - Similarity search
- `retrieve_chunks()` - Orchestrator returning QueryResponse
- `validate_results()` - Quality checking
- `run_single_query()` - Single query testing & logging
- `run_batch_test()` - Batch testing with aggregation

**No new dependencies**: All reuse Spec 001 (cohere, qdrant-client, python-dotenv)

**Estimated scope**: ~450-500 lines of well-documented Python code

**Testing approach**: Manual validation via query execution + batch test suite (no pytest framework for MVP)

---

## File Summary

| File | Status | Deliverable |
|------|--------|-------------|
| backend/retrieve.py | TO BUILD | Main implementation (6 functions) |
| backend/test_queries.json | TO CREATE | 10+ diverse test queries |
| backend/README.md | TO UPDATE | Retrieval section with examples |
| Test logs | GENERATED | test_results_YYYYMMDD_HHMMSS.log |

---

**Next**: Branch ready for implementation. BackendEngineer can begin with T001 prerequisite checks, then implement T003-T007 in parallel, followed by T008-T010 testing, and optional T011-T012 documentation.
