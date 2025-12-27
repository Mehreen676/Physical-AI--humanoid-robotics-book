---
id: 2
title: Hackathon Plan - Retrieval Testing Architecture
stage: plan
date: 2025-12-28
surface: agent
model: claude-haiku-4-5-20251001
feature: 002-rag-retrieval-testing
branch: 002-rag-retrieval-testing
user: Mehreen676
command: /sp.plan
labels: ["plan", "retrieval", "testing", "architecture", "rag", "hackathon", "cohere", "qdrant"]
links:
  spec: specs/002-rag-retrieval-testing/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-rag-retrieval-testing/plan.md
tests:
  - Constitution check - Principles alignment (5/5 PASS)
  - Constitution check - Technology compliance (3/3 PASS)
  - Architecture decisions documented (3 major decisions with rationale)
  - Data model definitions complete (4 entity types with validation rules)
  - API contracts defined (6 function signatures with clear inputs/outputs)
  - Implementation phases structured (10 detailed tasks with acceptance criteria)
  - Risk assessment completed (4 risks with mitigation strategies)
  - Success criteria mapped (all 10 from spec to implementation)
---

## Prompt

```text
rag-chatbot/PLAN_2_RETRIEVAL_TEST.md

Architecture decisions:
- Create single retrieve.py file in backend/ for all retrieval and testing logic
- retrieve.py: functions to encode query with Cohere, search Qdrant collection, retrieve top-k chunks, and validate with sample queries
- Use existing Qdrant collection from Spec 1
- @BackendEngineer → Implement RetrievalSkill in retrieve.py
- @Reviewer → Run validation with 10+ diverse queries and confirm front-end\docs\appendix\references.md
```

## Response snapshot

**Implementation Plan for Spec 002 – RAG Retrieval Testing Complete**

Successfully created comprehensive implementation plan for hackathon-focused RAG retrieval testing feature. Plan provides clear architecture, detailed data models, function contracts, and task breakdown ready for implementation.

### Architecture Overview

**Single Module Approach**: Single `retrieve.py` file in `backend/` directory containing all retrieval and testing logic.

**Key Design Decisions**:
1. **retrieve.py Module** - User requirement enforced; MVP scope doesn't need service separation; easy for judges to run
2. **Cohere Embeddings** - Same model as Spec 001 (`embed-english-light-v3.0`, 1024 dims) ensures query-chunk compatibility
3. **Qdrant Collection Querying** - Reuse existing "rag_embedding" collection from Spec 001; no new ingestion required

### Data Model Design

**Four Core Entities**:

1. **QueryRequest** (input):
   - query_text: str (3-5000 chars validation)
   - k: int (1-20 range, default 5)
   - timeout_seconds: int (1-30 range, default 10)

2. **RetrievedChunk** (individual result):
   - rank: int (1-based position)
   - similarity_score: float (0-1, from Qdrant cosine distance)
   - content: str (exact copy, no modification)
   - source_url: str (HTTP(S) URL)
   - chunk_position: int (position index)
   - created_at: str (ISO-8601 timestamp)

3. **QueryResponse** (complete result):
   - query: original text
   - query_embedding_dimension: 1024
   - timestamp: ISO-8601
   - k: requested top-k
   - results: List[RetrievedChunk]
   - result_count: actual count
   - execution_time_ms: end-to-end duration
   - status: "success" | "no_results" | "error"

4. **TestResultLog** (batch testing):
   - test_id: UUID
   - timestamp: ISO-8601
   - test_type: "single" | "batch"
   - queries_count: number of queries
   - results: List[QueryResponse]
   - statistics: {avg_score, min_score, max_score, avg_time, success_count, empty_count, error_count}

### API Contracts (6 Core Functions)

**Function 1: encode_query(query_text: str) -> List[float]**
- Converts query to Cohere embedding
- Returns 1024-dimensional vector
- Implements FR-001, SC-001

**Function 2: search_qdrant(embedding: List[float], k: int = 5, timeout: int = 10) -> List[dict]**
- Executes similarity search on "rag_embedding" collection
- Returns raw Qdrant results (to be formatted)
- Handles connection errors and timeouts
- Implements FR-002, SC-001

**Function 3: retrieve_chunks(query_text: str, k: int = 5) -> QueryResponse**
- Orchestrates encode + search + format
- Returns QueryResponse with all metadata
- Tracks execution time for SC-010
- Implements FR-001 through FR-005

**Function 4: validate_results(results: List[RetrievedChunk]) -> dict**
- Validates score ranges (0-1, descending order)
- Verifies content accuracy (matches stored chunks exactly)
- Checks metadata completeness (URL, position, timestamp)
- Returns validation report with metrics
- Implements FR-003, FR-004, SC-003, SC-005

**Function 5: run_single_query(query_text: str, k: int = 5, log_file: str = None) -> None**
- Executes single retrieval with validation
- Prints formatted JSON to console
- Logs to file with timestamp
- Includes execution time and validation metrics
- Implements FR-005, FR-008, SC-007, SC-008

**Function 6: run_batch_test(queries: List[str], k: int = 5, log_file: str = None) -> TestResultLog**
- Executes 10+ diverse test queries
- Aggregates results and calculates statistics
- Logs complete results with timestamps
- Returns TestResultLog for summary display
- Implements FR-010, SC-006, SC-007

### Implementation Phases

**Phase 1a: Core Retrieval** (T001-T003)
- T001: Implement encode_query() with Cohere API and retry logic
- T002: Implement search_qdrant() with error handling
- T003: Implement retrieve_chunks() orchestrator with timing

**Phase 1b: Validation & Formatting** (T004-T005)
- T004: Implement validate_results() with quality checks
- T005: Implement response formatting helpers for JSON output

**Phase 1c: Testing Functions** (T006-T007)
- T006: Implement run_single_query() with logging
- T007: Implement run_batch_test() with statistics

**Phase 2: Testing & Documentation** (T008-T010)
- T008: Create 10+ diverse test query suite
- T009: Run end-to-end testing validating all success criteria
- T010: Update README.md with retrieval documentation

### Constitution Alignment

✅ **ALL PRINCIPLES PASS**:

1. ✅ Technical Accuracy and Source Verification
   - Returns actual stored textbook content with source URLs (FR-004, SC-003)
   - No transformations or hallucinations

2. ✅ Clarity for Target Audience
   - CLI interface for judges with clean JSON output (FR-005, SC-008)
   - Clear logging for hackathon demo (FR-008, SC-007)

3. ✅ Reproducibility
   - All queries logged with timestamps (FR-008, SC-007)
   - Results verifiable against original textbook (SC-003)
   - Reuses Spec 001 infrastructure (no new dependencies)

4. ✅ Theory-Practice Integration
   - Tests practical retrieval against stored embeddings
   - Validates entire Spec 001 pipeline end-to-end

5. ✅ Standardized Citations
   - Includes source URLs and chunk positions for full traceability (FR-004, SC-005)

**GATE STATUS**: ✅ **PASS** — No violations; focused scope that validates existing infrastructure

### Project Structure

```
backend/
├── main.py              # Spec 001 (unchanged)
├── retrieve.py          # Spec 002 (NEW - 450-500 lines)
├── .env                 # Configuration (reused)
├── .env.example         # Template (reused)
├── .gitignore           # Already configured
├── README.md            # Updated with retrieve.py section
├── pyproject.toml       # No new dependencies
├── uv.lock              # Unchanged
└── .venv/               # Reused
```

### Risk Assessment & Mitigation

1. **Risk**: Qdrant collection empty if Spec 001 didn't run
   - **Mitigation**: Check collection size at startup; clear error message

2. **Risk**: API rate limits during batch testing
   - **Mitigation**: Exponential backoff retry (copy pattern from Spec 001)

3. **Risk**: Some queries >3 second limit on large collections
   - **Mitigation**: SC-010 allows 95th percentile; log slow queries; judge evaluates

4. **Risk**: Content accuracy subjective for book-specific queries
   - **Mitigation**: Include full chunks in logs; judges verify manually

### Success Criteria Mapping

✅ All 10 success criteria from specification mapped to implementation:

- SC-001: Similarity search returning top-k chunks → search_qdrant() + retrieve_chunks()
- SC-002: ≥90% relevant results → batch_test() aggregates metrics
- SC-003: 100% content accuracy → validate_results() checks exact match
- SC-004: Book-specific terminology → judged during T009 validation
- SC-005: 100% metadata inclusion → QueryResponse includes all fields
- SC-006: 10+ diverse queries covering modules → T008 creates query set
- SC-007: Results logged with timestamps → run_single_query() + run_batch_test()
- SC-008: Valid JSON formatting → retrieve_chunks() and formatting helpers
- SC-009: Edge cases handled → validate_results() + error handling in all functions
- SC-010: <3 seconds 95% of time → execution_time_ms tracked in QueryResponse

### Deliverables

**From /sp.plan**:
1. ✅ `specs/002-rag-retrieval-testing/plan.md` (comprehensive architecture)
2. ✅ Data model definitions (4 entities with validation rules)
3. ✅ API contracts (6 function signatures with inputs/outputs)
4. ✅ Implementation phases (10 tasks with acceptance criteria)
5. ✅ Risk assessment (4 risks with mitigation)
6. ✅ Success criteria mapping (all 10 to implementation)

**Generated Artifacts** (ready for next phase):
- Plan ready for `/sp.tasks` command to generate detailed task breakdown
- Architecture decisions documented for reference during implementation
- Clear function contracts for BackendEngineer role

## Outcome

- ✅ Impact: Comprehensive implementation plan created for Spec 002 retrieval testing feature with clear architecture (single retrieve.py module), detailed data models (4 entity types), API contracts (6 functions), and 10-task implementation breakdown aligned with hackathon demonstration goals and all 10 success criteria from specification.

- 🧪 Tests: Constitution check validated (8/8 items passed); architecture decisions documented with rationale (3 major decisions); data models complete with validation rules (4 entities); API contracts fully specified (6 functions with input/output/error handling); implementation phases structured (10 tasks with T001-T010 sequencing); risk assessment completed (4 risks with mitigations); success criteria mapped (all 10 from spec to implementation components).

- 📁 Files: `specs/002-rag-retrieval-testing/plan.md` created (416 lines comprehensive plan); PHR for planning work (this file) documenting architecture decisions, data models, function contracts, and task breakdown.

- 🔁 Next prompts: Run `/sp.tasks` command to generate detailed task breakdown with dependencies and time estimates; or `/sp.adr` to document architectural decisions if needed for future reference.

- 🧠 Reflection: Plan successfully translates specification into implementable architecture with clear single-module design (retrieve.py), proven pattern reuse from Spec 001 (Cohere API integration, exponential backoff retry), and explicit mapping of all success criteria to implementation components. Architecture is production-quality, focused, and aligned with hackathon demo requirements. Plan provides sufficient detail for BackendEngineer to implement without ambiguity while maintaining flexibility for testing and optimization decisions.

## Evaluation notes (flywheel)

- Failure modes observed: None - all architecture decisions have clear rationale; dependencies on Spec 001 properly scoped; no circular dependencies identified; success criteria clearly mappable to functions.

- Graders run and results (PASS/FAIL): PASS - Constitution check fully passed (all 5 principles + 3 tech compliance items); data models well-defined; function contracts clear and implementable; risk assessment comprehensive with mitigations; 10 success criteria explicitly mapped to implementation.

- Prompt variant (if applicable): null - single planning workflow with user's architecture direction (single retrieve.py) incorporated directly.

- Next experiment (smallest change to try): Proceed with `/sp.tasks` command to generate task breakdown; validate that tasks can be completed independently and in sequence; if task breakdown reveals dependencies not anticipated in plan, return to plan for clarification before implementation begins.
