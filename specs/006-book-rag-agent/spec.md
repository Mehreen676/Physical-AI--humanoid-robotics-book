# Feature Specification: BookRAGAgent — Multi-Agent Orchestration for Hallucination-Free RAG

**Feature Branch**: `006-book-rag-agent`
**Created**: 2025-12-30
**Status**: Draft
**Input**: User description: Complete BookRAGAgent orchestration system with sub-agents (Retrieval, Answer, Guardrails, SelectionMode, Memory) and skills (VectorSearch, SelectedTextOverride, GroundedSynthesis, RetrievalValidation, AntiHallucination, SessionPersistence)

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Query Book with Full RAG Pipeline (Priority: P1)

A user submits a natural language question. The BookRAGAgent orchestrates all sub-agents and skills to retrieve relevant book content, synthesize a grounded answer, validate against hallucination, and return the answer with citations. This is the core MVP—every other story depends on this flow working correctly.

**Why this priority**: Without a working RAG pipeline, the chatbot cannot answer user questions. This is the primary value proposition.

**Independent Test**: Can be fully tested by submitting a query, verifying that the system returns a grounded answer with citations from book content, and that no hallucinated content is present.

**Acceptance Scenarios**:

1. **Given** a user query "What is chapter 3 about?", **When** BookRAGAgent executes, **Then** the system returns a structured response with `answer`, `citations`, and `retrieved_chunks` with metadata (section, URL, chunk_id).
2. **Given** a valid book context in Qdrant, **When** RetrievalSubAgent searches for relevant chunks, **Then** VectorSearchSkill returns top-k chunks ranked by relevance with metadata preserved.
3. **Given** retrieved chunks, **When** AnswerSubAgent generates a response, **Then** GroundedSynthesisSkill synthesizes answer text that directly references retrieved chunks without inference.
4. **Given** a synthesized answer, **When** GuardrailsSubAgent runs, **Then** AntiHallucinationSkill vetos if answer contains inferred or external knowledge.

---

### User Story 2 - Selected-Text-Only Mode (Priority: P1)

A user highlights a passage in the book and asks a question with the constraint "answer only from this passage." The SelectionModeSubAgent intercepts the query, restricts retrieval scope to the selected passage only, and ensures the answer is drawn exclusively from that text. This enables trust-building by proving the system respects user-imposed constraints.

**Why this priority**: This is a key differentiator for user trust and a mandatory functional requirement from the constitution.

**Independent Test**: Can be fully tested by submitting a query with selected text metadata, verifying that RetrievalSubAgent restricts search to that passage, and that the answer is derived only from that passage.

**Acceptance Scenarios**:

1. **Given** a user query with `selected_text` parameter containing passage ID, **When** SelectionModeSubAgent receives the query, **Then** SelectedTextOverrideSkill overrides the vector search scope to filter only chunks matching that passage ID.
2. **Given** overridden retrieval scope, **When** RetrievalSubAgent executes, **Then** VectorSearchSkill returns only chunks from the selected passage.
3. **Given** limited chunks from selected passage, **When** AnswerSubAgent synthesizes, **Then** answer is entirely grounded in the selected passage or explicitly states "Not found in selected passage."

---

### User Story 3 - Multi-Turn Session Continuity (Priority: P2)

A user maintains a conversation with the chatbot over multiple turns. The MemorySubAgent preserves session history (recent N messages) without using conversation history as a retrieval source. Each new query can reference prior context but retrieval remains grounded in book content only.

**Why this priority**: Improves UX by enabling follow-up questions. Lower priority than core RAG because the system functions without it; enables the enhancement use case.

**Independent Test**: Can be fully tested by submitting multiple queries in sequence, verifying that SessionPersistenceSkill stores messages with user_id and session_id, and that context is available for subsequent queries without contaminating retrieval.

**Acceptance Scenarios**:

1. **Given** a user submits query Q1 and receives answer A1, **When** user submits follow-up query Q2 (e.g., "Tell me more"), **Then** MemorySubAgent retrieves prior conversation context.
2. **Given** prior conversation context, **When** Q2 is processed, **Then** context is used to disambiguate Q2, but RetrievalSubAgent searches only book content, not conversation history.
3. **Given** session storage in Neon PostgreSQL, **When** session persists, **Then** SessionPersistenceSkill stores messages with metadata (timestamp, user_id, session_id) and subsequent queries retrieve context deterministically.

---

### User Story 4 - Graceful Fallback When Content Missing (Priority: P1)

When a question cannot be answered from book content, the system does not hallucinate or infer external knowledge. Instead, it returns a clear, fact-based message that the answer cannot be found in the provided content and optionally suggests rephrasing.

**Why this priority**: This is critical to the zero-hallucination promise. Users must trust that "not found" means genuinely not found, not that the system is hiding information.

**Independent Test**: Can be fully tested by querying for content not in the book (e.g., "Who is the author's favorite pizza topping?") and verifying that the system returns the fallback message, not a made-up answer.

**Acceptance Scenarios**:

1. **Given** a query for which RetrievalSubAgent finds no relevant chunks (e.g., below similarity threshold), **When** AnswerSubAgent attempts synthesis, **Then** GuardrailsSubAgent vetos and returns: "The answer cannot be found in the provided book content. Please rephrase your question or try another topic."
2. **Given** an answer attempt that contains inferred or external knowledge, **When** AntiHallucinationSkill evaluates, **Then** it vetos the answer and fallback is returned.

### Edge Cases

- What happens when the user query is ambiguous (e.g., "it")? System MUST handle disambiguation gracefully by either requesting clarification or returning multiple relevant chunks.
- How does the system handle queries with special characters or non-English text? System MUST normalize input before vector search and either support the language or return a clear unsupported error.
- What happens if Qdrant returns no chunks (collection empty or service down)? System MUST return graceful fallback: "The book is not yet indexed. Please try again later."
- What happens if an external service (OpenRouter LLM, Qdrant, Neon) times out? System MUST log the failure without exposing service details and return: "Unable to process request. Please try again."
- What happens when retrieved chunks have inconsistent or corrupted metadata? System MUST validate metadata integrity before synthesis and skip chunks with invalid metadata.
- How does the system handle very long passages or very short user queries? System MUST apply reasonable bounds on input length (max query 500 chars, max chunk 2000 chars) to prevent LLM token overflow.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST accept user queries (natural language text, 1-500 characters) and optional selected_text parameter (passage ID or text range).
- **FR-002**: System MUST retrieve relevant book chunks from Qdrant vector database using semantic search, returning top-k results ranked by relevance score.
- **FR-003**: System MUST preserve metadata with every retrieved chunk: source URL, section name, chunk sequence ID, and original text hash.
- **FR-004**: System MUST restrict retrieval scope to selected passage only when selected_text parameter is provided (override VectorSearch scope).
- **FR-005**: System MUST synthesize answers exclusively from retrieved chunks without inference or external knowledge injection.
- **FR-006**: System MUST evaluate every answer against hallucination guardrails before returning to user; veto and return fallback if evaluation fails.
- **FR-007**: System MUST return structured JSON response with `answer`, `citations` (section, URL), and `retrieved_chunks` (text + metadata).
- **FR-008**: System MUST return fallback message "The answer cannot be found in the provided book content. Please rephrase your question or try another topic." when no answer can be grounded.
- **FR-009**: System MUST store chat sessions in Neon PostgreSQL with user_id, session_id, timestamp, and message history for multi-turn conversation support.
- **FR-010**: System MUST retrieve prior session context (recent N messages) for follow-up queries without contaminating retrieval with conversation history.
- **FR-011**: System MUST validate all environment variables at application startup (OPENROUTER_API_KEY, QDRANT_API_KEY, QDRANT_URL, NEON_DATABASE_URL, COLLECTION_NAME) and fail loudly with clear error messages if any are missing.
- **FR-012**: System MUST never log or expose API keys, tokens, or other secrets in responses, logs, or error messages.
- **FR-013**: System MUST handle external service failures (Qdrant timeout, LLM timeout, Database connection error) gracefully without exposing service details to the user.
- **FR-014**: System MUST apply input validation: query max 500 chars, chunk max 2000 chars, and reject or normalize non-ASCII characters based on embedding model support.
- **FR-015**: System MUST support multi-agent execution with clear step-by-step logging for debugging (without revealing secrets).

### Key Entities

- **User Query**: A natural language question, optional selected_text parameter (passage ID), optional session context (prior N messages). Immutable input.
- **Retrieved Chunk**: A text excerpt from the book, including metadata (source URL, section, chunk_id, similarity score, position in document). Primary unit of retrieval.
- **Session**: A conversation thread identified by session_id, associated with user_id and timestamp. Contains message history (user queries + system answers) for multi-turn context.
- **Chat Message**: A single message in a session (user query or system answer), with timestamp and metadata. Non-editable once persisted.
- **Structured Response**: JSON object returned to user: `{ answer: string, citations: [...], retrieved_chunks: [...] }`. The contract between system and client.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User Story 1 (Full RAG Pipeline) works end-to-end: user submits query, system returns structured JSON with answer, citations, and retrieved chunks. Zero manual intervention required.
- **SC-002**: Answer grounding rate ≥ 95%: System evaluates every answer against hallucination guardrails; at least 95% of returned answers are fully grounded in retrieved chunks with no inferred content.
- **SC-003**: Fallback accuracy: When queried for content not in the book, system returns fallback message ≥ 99% of the time (no hallucinated answers for off-topic queries).
- **SC-004**: User Story 2 (Selected-Text Mode) works correctly: When query includes selected_text parameter, system restricts retrieval to that passage only and answer is derived solely from that passage.
- **SC-005**: Session persistence: User Story 3 sessions are persisted deterministically in Neon PostgreSQL and retrieved accurately; follow-up queries maintain context without contaminating retrieval.
- **SC-006**: Response latency: System returns answer within 5 seconds of user query (assuming healthy external services). P95 latency under 10 seconds.
- **SC-007**: Metadata preservation: Every retrieved chunk is returned with complete metadata: source URL, section, chunk_id, and original text excerpt. No metadata is lost or corrupted.
- **SC-008**: Security compliance: No API keys, tokens, or secrets are logged, exposed in responses, or echoed in error messages. Environment variables validated at startup.
- **SC-009**: Error handling: All external service failures (Qdrant, LLM, Database) return user-friendly error messages without exposing service details or technical stack.
- **SC-010**: Multi-agent execution: All sub-agents (Retrieval, Answer, Guardrails, SelectionMode, Memory) are orchestrated correctly; execution logs show clear step-by-step flow for debugging.

## Assumptions

- **Embedding Model**: Cohere embeddings (or compatible embedding API) is used for vectorization. Chunks are pre-embedded and stored in Qdrant.
- **Similarity Threshold**: Vector search returns chunks with similarity score ≥ 0.7 by default; below this threshold, system treats query as unanswerable.
- **Session Retention**: Chat sessions are retained for 90 days by default; older sessions may be archived or deleted per data retention policy.
- **Concurrency**: System supports single-user sessions; multi-user concurrency is handled via session_id isolation (one session per user at a time).
- **Book Versioning**: Book content is immutable once ingested. Updated book versions require re-embedding and new collection creation; old chunks are marked as deprecated.
- **LLM Provider**: OpenRouter is the LLM provider for answer synthesis. OpenRouter API is the authoritative source for model availability and pricing.
- **External Service Health**: System assumes Qdrant, OpenRouter, and Neon are available with 99%+ uptime. Degraded services return friendly errors to users.
- **Deployment Context**: System is deployed as a FastAPI backend service with environment variables injected at runtime (not bundled with code).
- **Authentication**: User authentication and session management are handled by the frontend/wrapper layer; BookRAGAgent receives authenticated user_id and session_id.
