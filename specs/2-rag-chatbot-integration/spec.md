# Feature Specification: Integrated RAG Chatbot for Technical Book

## Overview

A production-ready, Retrieval-Augmented Generation (RAG) chatbot embedded directly into a published technical book enabling readers to:
- Query the full book content with intelligent retrieval and context-aware responses
- Perform text-selection-based queries using only user-highlighted passages
- Access chat history and conversation context
- Interact via an embeddable web UI

This feature transforms a static textbook into an interactive learning platform while maintaining strict factual accuracy through controlled RAG constraints.

---

## User Stories

### User Story 1: Reader Queries Full Book Content (Priority: P1)

A reader wants to ask a question about any topic in the book and receive an accurate, sourced answer based on the book's content.

**Why**: Readers often have questions while learning and need quick, accurate answers grounded in the textbook.

**Independent Test**: A reader can submit a query, and the chatbot returns a response with cited sources from the book.

**Acceptance Scenarios**:

1. **Given** a reader has the book open, **When** they ask "What are the key differences between ROS 2 and ROS 1?", **Then** the chatbot retrieves relevant sections and generates a response citing specific chapters.
2. **Given** a multi-turn conversation, **When** the reader follows up with "Can you elaborate on that?", **Then** the chatbot maintains context from previous messages.
3. **Given** a query with no relevant content, **When** the reader asks about external topics unrelated to the book, **Then** the chatbot responds: "I don't have information about that in the textbook. Please ask about topics covered in the book."

---

### User Story 2: Reader Queries Selected Text (Priority: P1)

A reader highlights a specific passage and asks a question that must be answered using ONLY that selected text.

**Why**: Readers need to understand specific passages and ensure the chatbot's understanding is limited to the selected context.

**Independent Test**: A reader selects text, enters a query, and the chatbot responds using only the selected passage.

**Acceptance Scenarios**:

1. **Given** a reader selects a paragraph about "Humanoid design principles", **When** they ask "What are the design principles mentioned here?", **Then** the chatbot answers using only that paragraph.
2. **Given** the selected text does not contain the answer, **When** the reader asks "How does this relate to motion control?", **Then** the chatbot responds: "The selected text does not contain the answer."
3. **Given** a longer selected passage (multiple paragraphs), **When** the reader asks a question, **Then** the chatbot uses all selected text to formulate the response.

---

### User Story 3: Reader Accesses Conversation History (Priority: P2)

A reader wants to save and retrieve previous conversations with the chatbot.

**Why**: Readers may want to revisit discussions or continue learning from past interactions.

**Independent Test**: A reader can view past conversations and resume from where they left off.

**Acceptance Scenarios**:

1. **Given** a reader has had multiple conversations, **When** they open the chatbot, **Then** a list of conversation sessions is displayed.
2. **Given** a reader selects a past conversation, **When** they click on it, **Then** the full message history and context are restored.

---

## Requirements *(mandatory)*

### Functional Requirements (FR)

#### Content Ingestion
- **FR-001**: The system MUST ingest chapters from Markdown files and chunk them intelligently based on heading hierarchy (H1→H3).
- **FR-002**: The system MUST extract embeddings for each chunk using OpenAI's embedding API.
- **FR-003**: The system MUST store embeddings in Qdrant Cloud with namespace per book/version.
- **FR-004**: The system MUST store document metadata (chapter, section, chunk_id, content, hash) in Neon Postgres.

#### Retrieval
- **FR-005**: The system MUST retrieve top-k (k=5) relevant chunks from Qdrant based on semantic similarity.
- **FR-006**: The system MUST support filtering by chapter/module via metadata in Qdrant.
- **FR-007**: The system MUST support selected-text mode where only user-provided passages are used for context.
- **FR-008**: The system MUST re-rank retrieved results by relevance score before generation.

#### Generation
- **FR-009**: The system MUST use OpenAI's gpt-4o (or specified model) to generate responses.
- **FR-010**: The system MUST enforce prompt constraints to prevent hallucination (e.g., "Answer ONLY based on retrieved context").
- **FR-011**: The system MUST cite sources (chapter/section) in responses.
- **FR-012**: The system MUST return "I don't have information about that in the textbook" if no relevant context exists.

#### API
- **FR-013**: The system MUST expose `/ingest` endpoint for adding/updating book content.
- **FR-014**: The system MUST expose `/query` endpoint for full-book queries.
- **FR-015**: The system MUST expose `/query-selected-text` endpoint for selected-text queries.
- **FR-016**: The system MUST expose `/health` endpoint for service status.
- **FR-017**: The system MUST support session management for conversation history.

#### Embedding
- **FR-018**: The system MUST provide a JavaScript SDK or iframe for embedding the chatbot in the Docusaurus book.
- **FR-019**: The system MUST support passing selected text from the book to the chatbot via window events or data attributes.
- **FR-020**: The system MUST display chat UI in a sidebar, modal, or dedicated panel within the book.

---

### Non-Functional Requirements (NFR)

- **NFR-001**: Retrieval latency MUST be ≤ 500ms (p95).
- **NFR-002**: Generation latency MUST be ≤ 5s (p95).
- **NFR-003**: Total query latency MUST be ≤ 6s (p95).
- **NFR-004**: System MUST support 100+ concurrent users on free-tier services.
- **NFR-005**: Error rate MUST be < 1%.
- **NFR-006**: All API keys MUST be stored in `.env` files; never hardcoded.
- **NFR-007**: Rate limiting MUST be implemented (e.g., 10 queries/min per session).
- **NFR-008**: Chat history MUST be encrypted at rest in Neon Postgres.
- **NFR-009**: System MUST log all queries and errors for observability.

---

## Key Entities

### Document & Chunk
```
{
  "doc_id": "string (UUID)",
  "doc_name": "string (chapter name)",
  "chapter": "string (e.g., 'Module 1')",
  "section": "string (e.g., 'ROS 2 Fundamentals')",
  "chunk_id": "integer (0-based)",
  "content": "string (up to 1000 tokens)",
  "embedding": "vector<1536> (OpenAI)",
  "hash": "string (for deduplication)",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Chat Message
```
{
  "message_id": "string (UUID)",
  "session_id": "string (UUID)",
  "user_message": "string",
  "assistant_response": "string",
  "source_chunks": "array of chunk_ids",
  "mode": "enum (full_book | selected_text)",
  "selected_text": "optional string (if mode=selected_text)",
  "created_at": "timestamp"
}
```

### Chat Session
```
{
  "session_id": "string (UUID)",
  "user_id": "optional string",
  "book_version": "string (e.g., 'v1.0')",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "message_count": "integer"
}
```

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: RAG accuracy on 20-query test set ≥ 90% (correct answers sourced from book).
- **SC-002**: Selected-text mode restricts responses to selected passages 100% of test cases.
- **SC-003**: Hallucination rate < 5% on out-of-scope queries.
- **SC-004**: API latencies meet NFR targets for p95.
- **SC-005**: Chatbot UI renders correctly in Docusaurus book on desktop and mobile.
- **SC-006**: Conversation history persistence verified with 5+ session resume tests.
- **SC-007**: Error handling tested for all edge cases (missing context, API failures, rate limits).

---

## Edge Cases & Error Handling

1. **Empty Query**: System returns "Please enter a question."
2. **No Relevant Context**: System returns "I don't have information about that in the textbook."
3. **API Failures** (OpenAI, Qdrant, Neon): System returns appropriate error with retry guidance.
4. **Rate Limit Exceeded**: System returns 429 with retry-after header.
5. **Malformed Selected Text**: System logs warning and falls back to full-book mode.
6. **Very Long Selected Text**: System truncates intelligently (up to 2000 tokens) with indication.

---

## Out of Scope

- Real-time collaborative features (multi-user editing).
- Integration with external knowledge bases (only book content).
- Voice-to-text input.
- Advanced NLP features (entity extraction, summarization beyond context).
- Custom fine-tuning of embedding models.

---

## Clarifications

### Session 2025-12-16

- **Q**: Should the selected-text mode truncate very long selections? **A**: Yes, intelligently to 2000 tokens, with user indication.
- **Q**: Should conversation history be per-session or per-user across sessions? **A**: Per-session initially; user-level aggregation can be added in v2.
- **Q**: What happens if the book is updated? Do embeddings require re-ingestion? **A**: Yes; hash-based deduplication avoids re-embedding unchanged chunks.
