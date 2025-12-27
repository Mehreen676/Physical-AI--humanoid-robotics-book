# Implementation Plan: RAG Retrieval Testing

**Branch**: `002-rag-retrieval-testing` | **Date**: 2025-12-28 | **Spec**: [specs/002-rag-retrieval-testing/spec.md](spec.md)

## Summary

Implement a retrieval and testing module (`retrieve.py`) that validates the RAG embedding pipeline. The module will convert text queries to Cohere embeddings, perform vector similarity searches against the Qdrant collection from Spec 001, retrieve top-k relevant chunks with complete metadata, and log results for comprehensive testing of retrieval accuracy across all textbook modules.

**Architecture**: Single `retrieve.py` file in `backend/` directory with functions for query encoding, Qdrant searching, result validation, and batch testing.

## Technical Context

**Language/Version**: Python 3.9+ (same as Spec 001)
**Primary Dependencies**: cohere, qdrant-client, python-dotenv (all reused from Spec 001)
**Storage**: Qdrant Cloud, existing collection "rag_embedding" from Spec 001
**Testing**: Manual query validation + batch test suite with logging
**Target Platform**: CLI execution (cross-platform: Windows, Linux, macOS)
**Project Type**: Single backend module
**Performance Goals**: <3 seconds end-to-end per query (95th percentile)
**Constraints**: Free tier API limits, pure semantic similarity (no reranking)
**Scale/Scope**: 10+ diverse test queries covering all textbook modules

## Constitution Check

✅ **PASS** — All principles aligned:
1. ✅ Technical Accuracy: Returns actual textbook content with source URLs (FR-004, SC-003)
2. ✅ Clarity for Audience: CLI interface with clean JSON output for judges (FR-005, SC-008)
3. ✅ Reproducibility: All queries logged; results verifiable (FR-008, SC-003)
4. ✅ Theory-Practice Integration: Tests Spec 001 pipeline end-to-end
5. ✅ Standardized Citations: Includes source URLs and positions (FR-004, SC-005)

## Phase 0: Research & Architecture Decisions

### Decision 1: Single retrieve.py Module

**Chosen**: Create single `retrieve.py` in `backend/`
**Rationale**:
- User requirement: "Create single retrieve.py file in backend/"
- MVP scope doesn't require service separation
- Easy for judges to run: `python backend/retrieve.py`
- Reuses .env config and Spec 001 collection

**Alternatives Rejected**:
- FastAPI server: Too complex for CLI testing
- Integrate into main.py: Separate concerns (ingestion vs retrieval)

### Decision 2: Cohere API for Query Encoding

**Chosen**: Use Cohere `embed-english-light-v3.0` (same as Spec 001)
**Rationale**:
- User requirement: "Cohere embeddings for query encoding"
- Consistency: Same model ensures compatibility with stored vectors
- 1024 dimensions match existing embeddings exactly
- Credentials already configured in .env

### Decision 3: Qdrant Collection Querying

**Chosen**: Query existing `rag_embedding` collection with top-k similarity search
**Rationale**:
- User requirement: "Use existing Qdrant collection from Spec 1"
- No new ingestion required; validates Spec 001 storage
- Return results as JSON with content, URL, similarity score, metadata

## Phase 1: Design & Data Model

### Data Models

**QueryRequest**:
- query_text: str (3-5000 chars)
- k: int (default 5, range 1-20)
- timeout_seconds: int (default 10)

**RetrievedChunk**:
- rank: int (1-based)
- similarity_score: float (0-1)
- content: str (exact copy from storage)
- source_url: str (HTTP(S) URL)
- chunk_position: int (position index)
- created_at: str (ISO-8601)

**QueryResponse**:
- query: str
- query_embedding_dimension: int (1024)
- timestamp: str (ISO-8601)
- k: int
- results: List[RetrievedChunk]
- result_count: int
- execution_time_ms: int
- status: str ("success" | "no_results" | "error")

**TestResultLog**:
- test_id: str (UUID)
- timestamp: str (ISO-8601)
- test_type: str ("single" | "batch")
- queries_count: int
- results: List[QueryResponse]
- statistics: {avg_score, min_score, max_score, avg_time, success_count, empty_count, error_count}

### API Contracts (Python Functions)

**Function 1: encode_query(query_text: str) -> List[float]**
- Input: Query text (3-5000 chars)
- Output: 1024-dimensional embedding vector
- Errors: ValueError for invalid length; APIError for Cohere unavailable
- Implements: FR-001, SC-001

**Function 2: search_qdrant(embedding: List[float], k: int = 5, timeout: int = 10) -> List[dict]**
- Input: Embedding vector, k, timeout
- Output: Raw search results from Qdrant
- Errors: ConnectionError, TimeoutError for Qdrant issues
- Implements: FR-002, SC-001

**Function 3: retrieve_chunks(query_text: str, k: int = 5) -> QueryResponse**
- Input: Query text, k
- Output: QueryResponse with formatted results
- Errors: Returns status="error" on failure
- Implements: FR-001 through FR-005, SC-001 through SC-008

**Function 4: validate_results(results: List[RetrievedChunk]) -> dict**
- Input: Retrieved chunks
- Output: Validation report {is_valid, checks_passed, issues}
- Validates: Score ranges, content accuracy, metadata completeness
- Implements: FR-003, FR-004, SC-003, SC-005

**Function 5: run_single_query(query_text: str, k: int = 5, log_file: str = None) -> None**
- Input: Query text, k, optional log file path
- Output: Prints JSON to console; appends to log file
- Implements: FR-005, FR-008, SC-007, SC-008

**Function 6: run_batch_test(queries: List[str], k: int = 5, log_file: str = None) -> TestResultLog**
- Input: List of queries (minimum 10), k, optional log file
- Output: TestResultLog with aggregated statistics
- Implements: FR-010, SC-006, SC-007

### Project Structure

```
backend/
├── main.py              # Spec 001: Embedding pipeline (unchanged)
├── retrieve.py          # Spec 002: Retrieval testing (NEW)
├── .env                 # Configuration (reused)
├── .env.example         # Template (reused)
├── .gitignore           # Already configured (includes *.log)
├── README.md            # Updated with retrieve.py docs
├── pyproject.toml       # No new dependencies needed
├── uv.lock              # Unchanged
└── .venv/               # Reused
```

## Phase 1: Implementation Tasks

### T001: Core Retrieval - encode_query()
**Purpose**: Convert user queries to Cohere embeddings
**Implementation**:
- Use cohere.ClientV2 (reuse from Spec 001)
- Validate query length (3-5000 chars)
- Add exponential backoff retry for rate limits (copy pattern from main.py)
- Return 1024-dimensional vector
**Acceptance**: Returns exactly 1024 dimensions; values in [-1,1] range

### T002: Core Retrieval - search_qdrant()
**Purpose**: Execute similarity search in Qdrant collection
**Implementation**:
- Use QdrantClient with existing QDRANT_URL, QDRANT_API_KEY
- Query "rag_embedding" collection with encoded query
- Handle k > collection size gracefully
- Implement timeout handling
- Add connection error logging
**Acceptance**: Returns results sorted by similarity descending; includes score and payload

### T003: Orchestration - retrieve_chunks()
**Purpose**: Combine encoding and searching into single function
**Implementation**:
- Call encode_query() for input
- Call search_qdrant() for search
- Format results as QueryResponse objects
- Track execution time
- Include timestamp (ISO-8601)
**Acceptance**: Returns QueryResponse with all fields; execution time <3000ms

### T004: Validation - validate_results()
**Purpose**: Verify retrieval quality and accuracy
**Implementation**:
- Check similarity scores in [0,1] range and sorted descending
- Verify content exactly matches stored chunks (no corruption)
- Validate metadata presence (URL, position, timestamp)
- Check JSON serialization
- Calculate accuracy metrics
**Acceptance**: All checks pass for valid results; identifies issues

### T005: Formatting - Response helpers
**Purpose**: Convert Qdrant results to QueryResponse JSON objects
**Implementation**:
- Build RetrievedChunk objects from Qdrant payloads
- Rank results (1-based indexing)
- Construct QueryResponse with all metadata
- Ensure JSON-serializable (no custom objects in output)
**Acceptance**: Valid JSON output; all required fields present

### T006: Testing - run_single_query()
**Purpose**: Execute and log single query for judge testing
**Implementation**:
- Call retrieve_chunks()
- Validate results with validate_results()
- Print formatted JSON to console
- Optionally log to file with timestamp
- Include execution time and validation metrics
**Acceptance**: JSON printed to console; matches schema; logged if requested

### T007: Testing - run_batch_test()
**Purpose**: Execute 10+ queries and aggregate results
**Implementation**:
- Iterate through queries list
- Execute retrieve_chunks() for each
- Aggregate results into TestResultLog
- Calculate statistics (avg, min, max scores; success rate)
- Log all results with timestamps
- Return TestResultLog for summary display
**Acceptance**: Processes all 10+ queries; calculates metrics; logs complete results

### T008: Test Suite - Create Query Set
**Purpose**: Design 10+ diverse test queries covering all modules
**Implementation**:
- Identify major modules/topics in textbook
- Create representative questions for each module
- Include edge cases (broad, narrow, ambiguous queries)
- Document expected topic coverage
- Ensure queries are judge-appropriate for demo
**Acceptance**: 10+ queries; covers all identified modules; documented

### T009: Validation - End-to-End Testing
**Purpose**: Run complete test suite and verify success criteria
**Implementation**:
- Execute batch_test() with full query suite
- Verify success criteria met (SC-001 through SC-010):
  - SC-001: Similarity search returning results ✓
  - SC-002: ≥90% relevant results (judge review)
  - SC-003: Content accuracy 100% (manual verification)
  - SC-004: Book-specific content (judge review)
  - SC-005: Metadata 100% complete ✓
  - SC-006: 10+ queries covering all modules ✓
  - SC-007: All results logged with timestamps ✓
  - SC-008: Valid JSON formatting ✓
  - SC-009: Edge cases handled (manual test)
  - SC-010: Response time <3s (measure during batch test)
- Log test run with date/time for hackathon demo
**Acceptance**: All success criteria verified; test results logged

### T010: Documentation - Update README
**Purpose**: Document how judges use retrieve.py
**Implementation**:
- Add "Retrieval Testing" section to backend/README.md
- Document function usage and parameters
- Include example queries and expected output
- Explain batch test results interpretation
- Document file locations for test logs
- Add troubleshooting for common issues
**Acceptance**: Clear instructions for judges to run retrieval tests independently

## Risk Assessment

**Risk 1**: Qdrant collection empty if Spec 001 didn't run
- **Mitigation**: Check collection size at startup; clear error message

**Risk 2**: API rate limits during batch testing
- **Mitigation**: Exponential backoff retry (proven pattern from Spec 001)

**Risk 3**: Some queries might exceed 3-second limit on large collections
- **Mitigation**: SC-010 allows 95th percentile; log slow queries; judge evaluates

**Risk 4**: Content accuracy subjective for book-specific queries
- **Mitigation**: Include full original chunk in logs; judges verify manually

## Success Criteria from Specification

✅ SC-001: Successful similarity search returning top-k chunks with scores
✅ SC-002: ≥90% of test queries return topically relevant results
✅ SC-003: Retrieved content matches source 100% accuracy
✅ SC-004: Book-specific content with proper terminology
✅ SC-005: 100% of results include complete metadata
✅ SC-006: Test suite covers all modules with 10+ queries
✅ SC-007: All queries and results logged with timestamps
✅ SC-008: Query responses valid, consistent JSON format
✅ SC-009: System handles edge cases appropriately
✅ SC-010: End-to-end retrieval <3 seconds (95% of time)

## Deliverables

**Phase 1 Outputs**:
1. `backend/retrieve.py` (450-500 lines with all 6 functions)
2. Updated `backend/README.md` with retrieval section
3. `research.md` with technical decisions documented
4. `data-model.md` with entity definitions
5. `quickstart.md` with judge usage guide
6. Test results logs (generated during T009)

**Next Phase**: `/sp.tasks` command to generate detailed task breakdown with dependencies
