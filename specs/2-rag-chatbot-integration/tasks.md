# Implementation Tasks: Integrated RAG Chatbot

**Feature**: RAG Chatbot Integration
**Feature Branch**: `2-rag-chatbot-integration`
**Total Tasks**: 28
**Dependency Order**: Sequential by phase; tasks within phases can be parallel.

---

## Phase 1: Core RAG Pipeline (8 tasks)

### Task 1.1: Set up FastAPI Backend Project

**Description**: Initialize FastAPI project with dependencies, folder structure, and configuration management.

**Acceptance Criteria**:
- [ ] FastAPI project initialized in `rag-backend/` directory.
- [ ] `requirements.txt` includes: fastapi, uvicorn, pydantic, python-dotenv, openai, qdrant-client, psycopg2, sqlalchemy.
- [ ] `.env.example` created with placeholders for API keys.
- [ ] `main.py` defines FastAPI app with CORS enabled.
- [ ] `config.py` loads environment variables and validates required keys.
- [ ] Health endpoint (`GET /health`) returns `{"status": "healthy"}`.
- [ ] Local development server starts without errors: `uvicorn main:app --reload`.

**Test Cases**:
- `curl http://localhost:8000/health` returns 200 OK.

**Estimated Effort**: 2 hours

---

### Task 1.2: Set up Qdrant Cloud Integration

**Description**: Configure Qdrant Cloud free tier account and Python client for vector operations.

**Acceptance Criteria**:
- [ ] Qdrant Cloud account created (free tier).
- [ ] API key stored in `.env`.
- [ ] Python client initialized: `from qdrant_client import QdrantClient`.
- [ ] Test collection created: `book_v1.0_chapters`.
- [ ] Helper function `create_qdrant_collection()` creates collection with HNSW index.
- [ ] Helper function `store_vectors()` stores 1536-dim embeddings with metadata.
- [ ] Helper function `query_vectors()` retrieves top-k results with scores.
- [ ] Integration test: Insert 10 test vectors; retrieve by similarity.

**Test Cases**:
- Insert vector with metadata; retrieve it with cosine similarity.
- Filter by metadata (e.g., chapter='Module 1'); verify results.

**Estimated Effort**: 3 hours

---

### Task 1.3: Set up Neon Postgres Integration

**Description**: Configure Neon Postgres free tier and SQLAlchemy ORM for data persistence.

**Acceptance Criteria**:
- [ ] Neon Postgres account created (free tier); connection string in `.env`.
- [ ] SQLAlchemy session factory configured.
- [ ] Models created: `Document`, `Session`, `Message`.
- [ ] Database migration script created (using Alembic).
- [ ] Tables created: `documents`, `sessions`, `messages`.
- [ ] Indexes created on `session_id`, `user_id`, `book_version`.
- [ ] Helper functions: `add_session()`, `add_message()`, `get_session_history()`.
- [ ] Integration test: Insert document, session, message; retrieve via queries.

**Test Cases**:
- Insert and retrieve session; verify message count.
- Query chat history for a session; verify message order.

**Estimated Effort**: 4 hours

---

### Task 1.4: Implement Embedding Generation (OpenAI)

**Description**: Create helper to generate embeddings via OpenAI API for chunks and queries.

**Acceptance Criteria**:
- [ ] Function `embed_text(text, model='text-embedding-3-small')` implemented.
- [ ] Handles batch embedding (up to 20 texts per call).
- [ ] Error handling: Retry on rate limit (3 retries, exponential backoff).
- [ ] Returns list of 1536-dim vectors.
- [ ] Cost tracking: Log tokens used per call.
- [ ] Unit test: Embed sample text; verify vector length = 1536.
- [ ] Unit test: Batch embed 5 texts; verify 5 vectors returned.
- [ ] Integration test: Embed first 100 words of book chapter.

**Test Cases**:
- Embed single text; verify cosine similarity to itself = 1.0.
- Embed two similar texts; verify cosine similarity > 0.8.

**Estimated Effort**: 2 hours

---

### Task 1.5: Implement Content Ingestion Endpoint (`POST /ingest`)

**Description**: Create endpoint to ingest chapters, chunk them intelligently, embed, and store in Qdrant + Neon.

**Acceptance Criteria**:
- [ ] Endpoint accepts chapter metadata (chapter, section, content).
- [ ] Chunking strategy: Split by H1/H2 headings; fallback to 800-token chunks.
- [ ] Hash-based deduplication: Skip if chunk hash exists in Neon.
- [ ] Generate embeddings for new chunks via OpenAI API.
- [ ] Store embeddings in Qdrant with metadata (doc_id, chapter, section, chunk_id).
- [ ] Store metadata in Neon `documents` table.
- [ ] Return JSON: `{ "ingested": N, "skipped": M, "vectors_stored": N }`.
- [ ] Endpoint protected (API key validation; optional for v1).
- [ ] Integration test: Ingest 3 sample chapters; verify 15+ chunks stored.

**Test Cases**:
- Ingest chapter; verify chunks stored in Qdrant and Neon.
- Re-ingest same chapter; verify duplicates skipped.
- Ingest oversized chapter (10k tokens); verify intelligent chunking.

**Estimated Effort**: 5 hours

---

### Task 1.6: Implement Retrieval Agent

**Description**: Create agent to embed query and retrieve top-k relevant chunks from Qdrant.

**Acceptance Criteria**:
- [ ] Function `retrieve_context(query, k=5, filters=None)` implemented.
- [ ] Embeds query using `embed_text()`.
- [ ] Queries Qdrant for top-k similar chunks (cosine similarity).
- [ ] Optionally filters by metadata (chapter, module).
- [ ] Returns list of chunks with scores, chapter, section.
- [ ] Handles case: No results (empty list returned; downstream handles).
- [ ] Unit test: Query "What is ROS 2?"; verify ROS-related chunks in top-5.
- [ ] Unit test: Query with metadata filter; verify results match filter.
- [ ] Latency test: Query latency ≤ 500ms (p95).

**Test Cases**:
- Query known topic in book; verify top result is relevant.
- Query irrelevant topic; verify results empty or low-confidence.

**Estimated Effort**: 3 hours

---

### Task 1.7: Implement Generation Agent with Prompt Templates

**Description**: Create agent to generate responses using OpenAI API with strict RAG constraints.

**Acceptance Criteria**:
- [ ] Function `generate_response(query, context_chunks, mode='full_book')` implemented.
- [ ] Constructs system prompt enforcing: "Answer ONLY based on provided context. If answer not in context, respond: 'I don't have information about that in the textbook.'"
- [ ] Constructs user prompt: `"Context:\n{context}\n\nQuestion: {query}"`.
- [ ] Calls OpenAI API (gpt-4o) with temperature=0.3 (low creativity).
- [ ] Extracts response text and formats with source citations.
- [ ] Handles out-of-context queries gracefully.
- [ ] Error handling: Fallback to gpt-3.5-turbo on failure.
- [ ] Unit test: Verify response based on provided context.
- [ ] Unit test: Verify out-of-context response triggers fallback message.
- [ ] Unit test: Verify response includes source citations.
- [ ] Latency test: Generation latency ≤ 5s (p95).

**Test Cases**:
- Generate response with 5 context chunks; verify answer is coherent and cites sources.
- Generate response with empty context; verify fallback message.

**Estimated Effort**: 4 hours

---

### Task 1.8: Implement `/query` Endpoint (Full Book Mode)

**Description**: Create endpoint combining retrieval and generation for full-book queries.

**Acceptance Criteria**:
- [ ] POST `/query` endpoint accepts: `{ "query": "...", "session_id": "...", "filters": {...} }`.
- [ ] Calls `retrieve_context(query, filters)`.
- [ ] Calls `generate_response(query, context)`.
- [ ] Creates session if not exists; logs message to Neon.
- [ ] Returns JSON: `{ "response": "...", "sources": [...], "session_id": "...", "latency_ms": N }`.
- [ ] Rate limiting: 10 queries/min per session (implement with request counter or Redis).
- [ ] Error handling: Returns 400 for empty query, 429 for rate limit.
- [ ] Integration test: Query full book; verify response with sources.
- [ ] Load test: 20 concurrent queries; all succeed within latency budget.

**Test Cases**:
- Query known topic; verify response ≤ 6s.
- Query rate limit; verify 429 returned on 11th query/min.

**Estimated Effort**: 4 hours

---

## Phase 2: Selected-Text Mode & Chat UI (7 tasks)

### Task 2.1: Implement `/query-selected-text` Endpoint

**Description**: Create endpoint for answering questions using only user-selected text.

**Acceptance Criteria**:
- [ ] POST `/query-selected-text` endpoint accepts: `{ "query": "...", "selected_text": "...", "session_id": "..." }`.
- [ ] Validates selected_text length (max 2000 tokens; truncate if needed).
- [ ] Embeds selected text to get vector representation.
- [ ] Generates response using selected text as sole context.
- [ ] Server-side validation: Verifies response context is within selected text (prompt-enforced).
- [ ] Returns: `{ "response": "...", "in_selected_text": true/false, "sources": [...] }`.
- [ ] If no answer in selected text: `{ "response": "The selected text does not contain the answer.", "in_selected_text": false }`.
- [ ] Error handling: Empty selected_text returns 400.
- [ ] Integration test: Select paragraph; query it; verify response uses only that paragraph.

**Test Cases**:
- Select text with answer; query it; verify answer extracted.
- Select text without answer; query unrelated topic; verify fallback message.

**Estimated Effort**: 3 hours

---

### Task 2.2: Create JavaScript SDK (`chat-embed.js`)

**Description**: Build lightweight JavaScript SDK for embedding chatbot in Docusaurus and capturing text selection.

**Acceptance Criteria**:
- [ ] File: `rag-backend/sdk/chat-embed.js` created.
- [ ] Exports `RagChatbot` class with methods: `init()`, `query()`, `querySelectedText()`, `getSessionHistory()`.
- [ ] `init()` accepts config: `{ apiUrl, sessionId, onMessage, onError }`.
- [ ] Text selection listener: `document.addEventListener('selectionchange', ...)` captures selected text.
- [ ] Method `querySelectedText()` extracts selection and calls backend.
- [ ] Method `query()` calls `/query` endpoint.
- [ ] Session storage via `localStorage` (persists session_id across page reloads).
- [ ] Error handling: Retry failed requests; notify user on error.
- [ ] Unit test: SDK initializes without errors.
- [ ] Unit test: Query returns response; message displayed.

**Test Cases**:
- Initialize SDK with mock backend; verify callbacks work.
- Simulate text selection; verify selected text captured.

**Estimated Effort**: 4 hours

---

### Task 2.3: Create React Chat UI Component

**Description**: Build React component for displaying chat UI in Docusaurus.

**Acceptance Criteria**:
- [ ] Component file: `docusaurus_textbook/src/components/RagChatbot.jsx`.
- [ ] Displays chat messages in scrollable list.
- [ ] Input field for user queries.
- [ ] Button to query selected text (enabled only if text selected).
- [ ] Displays loading state during query.
- [ ] Displays error messages on API failure.
- [ ] Displays citations (chapter, section) below each response.
- [ ] Responsive design (mobile + desktop).
- [ ] WCAG 2.1 AA accessibility compliance (ARIA labels, keyboard navigation).
- [ ] Unit test: Component renders without errors.
- [ ] Unit test: Send message; verify message displayed.

**Test Cases**:
- Render component; verify UI elements visible.
- Type message; press Send; verify message sent and response displayed.

**Estimated Effort**: 5 hours

---

### Task 2.4: Integrate Chat UI into Docusaurus

**Description**: Embed chat component into Docusaurus layout (sidebar or modal).

**Acceptance Criteria**:
- [ ] Chat component integrated into `docusaurus_textbook/docusaurus.config.js` or theme wrapper.
- [ ] Chat UI appears as sidebar on right side of page (desktop) or bottom sheet (mobile).
- [ ] Can be toggled open/closed via button in navbar or floating action button.
- [ ] Does not obstruct book content.
- [ ] API endpoint URL configurable via environment variable.
- [ ] Session ID passed from frontend to backend.
- [ ] Integration test: Navigate to book chapter; chat sidebar visible and clickable.

**Test Cases**:
- Load book chapter; verify chat sidebar visible.
- Click chat toggle; verify sidebar opens/closes.

**Estimated Effort**: 3 hours

---

### Task 2.5: Implement Text Selection Capture & Highlighting

**Description**: Enhance UI to capture selected text and visually highlight it.

**Acceptance Criteria**:
- [ ] When user selects text in book, selection event captured.
- [ ] Selected text visually highlighted (e.g., yellow background).
- [ ] "Ask about this" button appears next to selection.
- [ ] Clicking button pre-fills chat input with selected text (option to edit).
- [ ] Chat query automatically uses selected-text mode.
- [ ] Clears highlight when new text selected or highlight dismissed.
- [ ] Works across multiple paragraphs (multiline selection).
- [ ] Unit test: Select text; verify highlight applied.
- [ ] Unit test: Verify selection passed to API in selected-text mode.

**Test Cases**:
- Select single sentence; verify highlight and button appear.
- Select multiple paragraphs; verify all highlighted.

**Estimated Effort**: 3 hours

---

### Task 2.6: Implement Client-Side Validation & Input Sanitization

**Description**: Add validation for query and selected text inputs to prevent abuse/errors.

**Acceptance Criteria**:
- [ ] Query max length: 500 chars (enforced in UI and API).
- [ ] Selected text max length: 10k chars (truncate with user indication).
- [ ] Input sanitization: Remove HTML, scripts (XSS prevention).
- [ ] Warn user if query or selected text invalid before sending.
- [ ] API returns 400 on invalid input.
- [ ] Unit test: Oversized query rejected.
- [ ] Unit test: Malformed input sanitized.

**Test Cases**:
- Enter 501-char query; verify error and prevented submission.
- Paste HTML in selected text; verify sanitized and truncated.

**Estimated Effort**: 2 hours

---

### Task 2.7: Implement Server-Side Context Validation (Selected-Text Mode)

**Description**: Validate that generated response uses only selected text (defense in depth).

**Acceptance Criteria**:
- [ ] Function `validate_response_in_context(response, selected_text)` implemented.
- [ ] Uses semantic similarity to check if response concepts are in selected text.
- [ ] If validation fails, replaces response with fallback message.
- [ ] Logs warnings for failed validations (potential issue).
- [ ] Unit test: Response using selected text passes validation.
- [ ] Unit test: Response using external knowledge fails validation (replaced with fallback).

**Test Cases**:
- Generate response within selected text; verify validation passes.
- Force response outside context; verify validation fails and fallback applied.

**Estimated Effort**: 3 hours

---

## Phase 3: Session Management & History (4 tasks)

### Task 3.1: Implement Session Management

**Description**: Create session lifecycle management (create, retrieve, update, delete).

**Acceptance Criteria**:
- [ ] Function `create_session(user_id=None, book_version='v1.0')` creates entry in `sessions` table.
- [ ] Returns `session_id` UUID.
- [ ] Function `get_session(session_id)` retrieves session.
- [ ] Function `update_session(session_id)` updates `updated_at` timestamp.
- [ ] Session auto-expires after 30 days of inactivity (configurable).
- [ ] Unit test: Create and retrieve session.
- [ ] Unit test: Session message count incremented on new message.

**Test Cases**:
- Create session; verify session_id returned and stored.
- Query session; verify metadata accurate.

**Estimated Effort**: 2 hours

---

### Task 3.2: Implement Chat History Persistence

**Description**: Store and retrieve chat messages with session association.

**Acceptance Criteria**:
- [ ] Function `add_message(session_id, user_message, assistant_response, sources, mode)` creates message record.
- [ ] Stores: message content, source chunks, query mode, timestamp.
- [ ] Function `get_messages(session_id, limit=50)` retrieves messages for session (paginated).
- [ ] Messages returned in chronological order.
- [ ] Encryption at rest: Sensitive fields encrypted (optional for v1; use `cryptography` library).
- [ ] Unit test: Add message; retrieve it.
- [ ] Unit test: Retrieve 50+ messages; verify pagination.

**Test Cases**:
- Add 10 messages to session; retrieve all; verify order.
- Retrieve messages with limit; verify pagination works.

**Estimated Effort**: 3 hours

---

### Task 3.3: Implement GET `/sessions/{session_id}` Endpoint

**Description**: Expose session and chat history via API.

**Acceptance Criteria**:
- [ ] GET `/sessions/{session_id}` returns session metadata and messages.
- [ ] Response schema: `{ "session_id": "...", "created_at": "...", "messages": [...], "message_count": N }`.
- [ ] Each message includes: `{ "message_id", "user_message", "assistant_response", "sources", "created_at" }`.
- [ ] Optional query param `?limit=50` for pagination.
- [ ] 404 if session not found.
- [ ] Unit test: Retrieve existing session; verify data.
- [ ] Unit test: Query nonexistent session; verify 404.

**Test Cases**:
- Create session with 5 messages; GET /sessions/{id}; verify all messages returned.

**Estimated Effort**: 2 hours

---

### Task 3.4: Implement LocalStorage Caching for Sessions

**Description**: Cache recent session history in browser for offline access.

**Acceptance Criteria**:
- [ ] JavaScript SDK stores recent sessions in `localStorage`.
- [ ] Key: `rag_sessions`; value: list of session IDs + metadata.
- [ ] Auto-sync: When online, fetch latest messages from backend and update cache.
- [ ] When offline, display cached messages with indication.
- [ ] Cache max size: 10 sessions; evict oldest on overflow.
- [ ] Unit test: Store session in localStorage; retrieve it.
- [ ] Unit test: Sync online session with backend.

**Test Cases**:
- Store 5 sessions in localStorage; verify all retrievable.
- Go offline; verify cached sessions still accessible.

**Estimated Effort**: 2 hours

---

## Phase 4: Testing, Optimization & Deployment (9 tasks)

### Task 4.1: Create RAG Accuracy Test Suite

**Description**: Build test suite to validate RAG accuracy on diverse queries.

**Acceptance Criteria**:
- [ ] Test dataset: 20 queries covering all book modules (e.g., "What is ROS 2?", "Explain humanoid design", "What is VLA?").
- [ ] Expected answers documented for each query.
- [ ] Test script executes all queries; logs results (correct/incorrect).
- [ ] Accuracy metric: Correct answers / Total queries.
- [ ] Target: ≥ 90% accuracy (18/20 correct).
- [ ] CI/CD integration: Run tests on each commit; fail if accuracy drops.
- [ ] Unit test: Individual query accuracy checked.

**Test Cases**:
- Run test suite; verify 18+ answers correct.
- Modify RAG prompt; run tests; verify no regression.

**Estimated Effort**: 4 hours

---

### Task 4.2: Create Selected-Text Mode Test Suite

**Description**: Validate selected-text mode restricts responses correctly.

**Acceptance Criteria**:
- [ ] Test dataset: 20 selected-text queries with known answers in text.
- [ ] Test dataset: 10 queries where answer NOT in selected text.
- [ ] Test script: For first 20, verify answer extracted; for second 10, verify fallback message.
- [ ] Success metric: 30/30 tests pass (100% restriction).
- [ ] CI/CD integration: Run tests on each commit.

**Test Cases**:
- Select chapter section; query contained in it; verify answer extracted.
- Select chapter section; query NOT in it; verify fallback message.

**Estimated Effort**: 3 hours

---

### Task 4.3: Create Latency & Performance Test Suite

**Description**: Benchmark and validate performance against NFR targets.

**Acceptance Criteria**:
- [ ] Test harness: Send 50 queries; measure retrieval, generation, and total latency.
- [ ] Calculate p50, p95, p99 latencies.
- [ ] Targets: Retrieval p95 ≤ 500ms; Generation p95 ≤ 5s; Total p95 ≤ 6s.
- [ ] Log results; fail if any target exceeded.
- [ ] Profile API bottlenecks; optimize hotspots.
- [ ] CI/CD integration: Run on commit; alert on regression.

**Test Cases**:
- Run load test; verify all latencies within budget.
- Identify slowest API call; optimize; re-run; verify improvement.

**Estimated Effort**: 4 hours

---

### Task 4.4: Create Load Test Suite (Concurrent Users)

**Description**: Stress test API with concurrent users; verify stability and error rate.

**Acceptance Criteria**:
- [ ] Load test: 100 concurrent users; each sends 10 queries (1000 total).
- [ ] Measure: Error rate, p95 latency, CPU/memory usage.
- [ ] Success criteria: Error rate < 1%; latency degradation < 20%.
- [ ] Identify bottleneck (Qdrant, OpenAI, Neon, FastAPI).
- [ ] Implement optimizations (caching, pooling, scaling).
- [ ] Re-run test; verify success criteria met.

**Test Cases**:
- Simulate 50 users; verify error rate < 1%.
- Simulate 100 users; verify latency degradation < 20%.

**Estimated Effort**: 5 hours

---

### Task 4.5: Implement Caching Layer (Redis Optional)

**Description**: Add caching to reduce latency and cost (optional for free tier).

**Acceptance Criteria**:
- [ ] Cache layer: Cache frequently asked queries (e.g., "What is ROS 2?") and their responses.
- [ ] Implementation: Use Neon as cache (row-level) or add Redis (optional).
- [ ] TTL: 24 hours (configurable).
- [ ] Cache hit rate metric: Track and log.
- [ ] Unit test: Cache hit returns cached response.
- [ ] Unit test: Cache miss queries backend.

**Test Cases**:
- Query same topic twice; verify second query returns from cache.
- Cache expires; verify query re-runs backend.

**Estimated Effort**: 3 hours

---

### Task 4.6: Implement Security Hardening

**Description**: Add API key validation, CORS, input validation, rate limiting enforcement.

**Acceptance Criteria**:
- [ ] API key validation: All admin endpoints (`/ingest`) require valid API key (X-API-Key header).
- [ ] CORS configured: Allow requests only from book domain.
- [ ] Input validation: Query max 500 chars; selected text max 10k chars.
- [ ] Sanitization: Remove HTML/scripts from inputs.
- [ ] Rate limiting: 10 queries/min per session; 1000/day per IP.
- [ ] Error messages: Do not expose sensitive data (e.g., query internals).
- [ ] HTTPS enforced: All endpoints require TLS 1.3.
- [ ] Unit test: Missing API key returns 401.
- [ ] Unit test: Rate limit exceeded returns 429.
- [ ] Unit test: XSS attempt in query sanitized.

**Test Cases**:
- Call /ingest without API key; verify 401.
- Send 11 queries in 1 min; verify 11th returns 429.
- Inject HTML in query; verify sanitized.

**Estimated Effort**: 3 hours

---

### Task 4.7: Create Observability & Monitoring

**Description**: Add logging, metrics, and alerting for production readiness.

**Acceptance Criteria**:
- [ ] Structured logging: All API requests, Qdrant queries, OpenAI calls logged with request ID, latency, status.
- [ ] Log format: JSON; include user_id, session_id, query_id for tracing.
- [ ] Metrics: Prometheus-compatible metrics (retrieval latency, generation latency, error rate).
- [ ] Alerting: Alert if error rate > 1%, latency p95 > 8s, API key quota exceeded.
- [ ] Dashboard: Simple dashboard showing real-time metrics (optional; use Grafana if available).
- [ ] Cost tracking: Log OpenAI tokens used per query; alert if daily spend > threshold.
- [ ] Unit test: Log message includes all required fields.

**Test Cases**:
- Run query; verify log entry created with all fields.
- Trigger error; verify error logged and alert sent.

**Estimated Effort**: 4 hours

---

### Task 4.8: Create Deployment Guide & Runbooks

**Description**: Document deployment process, scaling, troubleshooting, and rollback procedures.

**Acceptance Criteria**:
- [ ] Deployment guide: Step-by-step to deploy FastAPI backend to serverless host (Render/Railway).
- [ ] Environment variables documented.
- [ ] Database migration guide (Alembic).
- [ ] Scaling guide: Instructions to upgrade Qdrant/Neon to paid tiers if needed.
- [ ] Troubleshooting runbook: Common issues (API failure, rate limit, latency spike) and solutions.
- [ ] Rollback procedure: How to roll back to previous version.
- [ ] Disaster recovery: Backup/restore procedures for Neon data.
- [ ] Document code references where applicable (e.g., "See deployment logic in `main.py:L42`").

**Estimated Effort**: 3 hours

---

### Task 4.9: Create Documentation & User Guide

**Description**: Write comprehensive documentation for users and developers.

**Acceptance Criteria**:
- [ ] User Guide: How to use chat in book (asking questions, selecting text, viewing history).
- [ ] Developer Guide: How to extend RAG chatbot (add new data sources, customize prompts).
- [ ] API Documentation: OpenAPI/Swagger schema auto-generated from FastAPI.
- [ ] Architecture documentation: System overview, data flow, decision rationale.
- [ ] Limitations: Clearly state what chatbot can/cannot do.
- [ ] FAQ: Common questions answered.
- [ ] Readme: Quick start guide.

**Estimated Effort**: 3 hours

---

## Phase 4 (Continued): Quality Assurance (Inlined with Above)

### Integration Tests

**Acceptance Criteria**:
- [ ] End-to-end test: Ingest chapter → Query it → Verify response with sources.
- [ ] UI test: Open book → Select text → Ask question → Verify answer displayed.
- [ ] Session test: Create session → Add 5 messages → Retrieve history → Verify all messages.
- [ ] Cross-browser test: Chrome, Firefox, Safari (desktop + mobile).

### Accessibility Tests

**Acceptance Criteria**:
- [ ] WCAG 2.1 AA compliance verified (via axe-core or similar).
- [ ] Keyboard navigation: Tab through all UI elements; Enter submits query.
- [ ] Screen reader: Chat messages readable; ARIA labels present.
- [ ] Color contrast: Text meets WCAG contrast ratios.

### Security Tests

**Acceptance Criteria**:
- [ ] Penetration test: Try SQL injection, XSS, auth bypass; all blocked.
- [ ] API key not exposed in git history: `git log -S` for secrets.
- [ ] Dependencies scanned for vulnerabilities: `pip audit`, `npm audit`.
- [ ] Sensitive data (API keys) never in logs or error messages.

---

## Dependency Graph

```
Phase 1 (Core RAG Pipeline):
  1.1 FastAPI Setup
    ├→ 1.2 Qdrant Integration
    ├→ 1.3 Neon Integration
    ├→ 1.4 Embedding Generation
    │   ├→ 1.5 Ingest Endpoint
    │   │   └→ 1.6 Retrieval Agent
    │   │       └→ 1.7 Generation Agent
    │   │           └→ 1.8 /query Endpoint

Phase 2 (Selected-Text & UI): [Depends on Phase 1]
  2.1 /query-selected-text Endpoint [Depends on 1.7, 1.8]
    ├→ 2.2 JavaScript SDK
    │   ├→ 2.3 React UI Component
    │   │   ├→ 2.4 Docusaurus Integration
    │   │   ├→ 2.5 Text Selection Capture
    │   │   ├→ 2.6 Input Validation
    │   │   └→ 2.7 Server-Side Validation

Phase 3 (Session Management): [Depends on Phase 1 & 2]
  3.1 Session Management [Depends on 1.3]
    ├→ 3.2 Chat History Persistence
    │   ├→ 3.3 /sessions Endpoint
    │   └→ 3.4 LocalStorage Caching

Phase 4 (Testing & Deployment): [Depends on Phases 1-3]
  4.1 RAG Accuracy Tests
  4.2 Selected-Text Tests
  4.3 Latency/Performance Tests
  4.4 Load Tests
  4.5 Caching (Optional)
  4.6 Security Hardening
  4.7 Observability
  4.8 Deployment Guide
  4.9 Documentation
```

---

## Notes

- **Parallel Execution**: Tasks within same phase can run in parallel (e.g., 1.2, 1.3, 1.4 can be parallel after 1.1).
- **Code References**: All code should reference implementation locations (e.g., `main.py:L142`).
- **Test Coverage**: Aim for 80%+ code coverage; use `pytest` with `coverage` plugin.
- **Documentation**: Keep code documentation in docstrings; reference in acceptance criteria.
- **Version Control**: Feature branch `2-rag-chatbot-integration`; each task a separate commit.
