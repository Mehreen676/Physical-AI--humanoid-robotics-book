# Data Model: BookRAGAgent

**Date**: 2025-12-30 | **Status**: Phase 1 Design | **Version**: 1.0

## Overview

This document defines the data entities used by BookRAGAgent for session management, chat history, and API contracts. The model is designed for simplicity (SQL-backed, minimal denormalization) and supports the core feature of multi-turn RAG conversations.

---

## Entity Diagram

```
┌─────────────┐
│   User      │
├─────────────┤
│ user_id (PK)│◄──────┐
│ created_at  │       │
└─────────────┘       │
                      │
               ┌──────┴────────┐
               │   Session    │
               ├──────────────┤
               │session_id(PK)│
               │user_id (FK)  │◄────┐
               │created_at    │     │
               │updated_at    │     │
               │metadata(JSON)│     │
               └──────────────┘     │
                                    │
                          ┌─────────┴────────┐
                          │  ChatMessage     │
                          ├──────────────────┤
                          │message_id (PK)   │
                          │session_id (FK)   │
                          │role (enum)       │
                          │content (text)    │
                          │metadata (JSON)   │
                          │created_at        │
                          └──────────────────┘
```

---

## Entities

### 1. User

Represents an authenticated user (optional, for multi-user scenarios).

**Table Name**: `users`

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| user_id | UUID | PRIMARY KEY | Unique identifier (typically JWT sub claim) |
| created_at | TIMESTAMP | NOT NULL | When user first accessed the system |

**Relationships**:
- One User has many Sessions (1:N)

**Indexes**:
- PRIMARY KEY on user_id

**Notes**:
- Optional if system is single-user (user_id can be hardcoded)
- Populated by authentication layer (not by BookRAGAgent)

---

### 2. Session

Represents a conversation thread (one session per user at a time, or per browser tab in multi-tab scenario).

**Table Name**: `sessions`

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| session_id | UUID | PRIMARY KEY | Unique identifier for this conversation |
| user_id | UUID | FOREIGN KEY (users.user_id) | Who owns this session |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When session started |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last message timestamp |
| metadata | JSONB | NULL | Client metadata (e.g., { "tab_id": "...", "theme": "dark" }) |

**Relationships**:
- One Session belongs to one User (N:1)
- One Session has many ChatMessages (1:N)

**Indexes**:
- PRIMARY KEY on session_id
- FOREIGN KEY on user_id
- INDEX on user_id (for query: "Get all sessions for user X")

**Constraints**:
- session_id must be unique across all users
- user_id cannot be NULL (enforces ownership)

**Notes**:
- `updated_at` is used to determine "last active" and for cleanup/archival
- `metadata` is flexible JSON for future extensions (client state, preferences, etc.)

---

### 3. ChatMessage

Represents a single message in a session (user query OR assistant response).

**Table Name**: `chat_messages`

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| message_id | UUID | PRIMARY KEY | Unique identifier for this message |
| session_id | UUID | FOREIGN KEY (sessions.session_id) | Which session this belongs to |
| role | ENUM('user', 'assistant') | NOT NULL | Who sent this message |
| content | TEXT | NOT NULL | The actual message text |
| metadata | JSONB | NULL | Message-specific metadata |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When message was created |

**Relationships**:
- Many ChatMessages belong to one Session (N:1)

**Indexes**:
- PRIMARY KEY on message_id
- FOREIGN KEY on session_id
- INDEX on (session_id, created_at) (for query: "Get last N messages for session X")

**Constraints**:
- session_id cannot be NULL
- role must be 'user' or 'assistant'
- content cannot be NULL

**Metadata JSON Schema** (informational, not enforced at DB level):
```json
{
  "chunks_used": ["chunk-id-1", "chunk-id-2"],
  "similarity_scores": [0.85, 0.72],
  "latency_ms": 1234,
  "tokens": {"input": 256, "output": 128},
  "selected_text_mode": false,
  "error": null
}
```

**Notes**:
- User messages: role='user', content is the question
- Assistant messages: role='assistant', content is the answer JSON (stringified)
- Metadata captures retrieval details (chunks, scores, performance) for debugging
- `created_at` preserves message order within session

---

### 4. RetrievedChunk (In-Memory)

Represents a chunk of book content retrieved from Qdrant. NOT stored in database (in-memory during request).

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| chunk_id | string | Unique identifier within Qdrant collection |
| text | string | The actual chunk content (up to 2000 chars) |
| metadata | dict | Metadata from Qdrant: url, section, position, embedding_score |

**Origin**: Retrieved from Qdrant Cloud during VectorSearchSkill execution

**Lifetime**: Ephemeral (request scope only)

**Usage**:
- Passed to GroundedSynthesisSkill for answer synthesis
- Returned to user in /chat response under "retrieved_chunks"
- Logged to ChatMessage.metadata for traceability

**Example**:
```json
{
  "chunk_id": "chunk-00042",
  "text": "Chapter 3 discusses the fundamentals of neural networks...",
  "metadata": {
    "url": "https://book.example.com/chapter-3",
    "section": "Chapter 3: Neural Networks",
    "position": 2,
    "embedding_score": 0.8754
  }
}
```

---

### 5. Pydantic Models (API Contracts)

These are Python/JSON models for request/response validation.

#### ChatRequest

**Input to /chat endpoint**

```python
from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    question: str  # 1-500 chars
    session_id: str  # UUID
    selected_text: Optional[str] = None  # Optional passage restriction
```

#### Citation

**Part of ChatResponse**

```python
class Citation(BaseModel):
    section: str  # e.g., "Chapter 3: Neural Networks"
    url: str  # e.g., "https://book.example.com/chapter-3"
```

#### RetrievedChunkResponse

**Part of ChatResponse**

```python
from typing import Dict, Any

class RetrievedChunkResponse(BaseModel):
    text: str  # The chunk content
    metadata: Dict[str, Any]  # url, section, chunk_id, embedding_score, position
```

#### ChatResponse

**Output from /chat endpoint**

```python
class ChatResponse(BaseModel):
    answer: str  # The grounded answer
    citations: List[Citation]  # Sources for the answer
    retrieved_chunks: List[RetrievedChunkResponse]  # All chunks used
```

**Example Response**:
```json
{
  "answer": "Chapter 3 covers neural network fundamentals, including perceptrons, activation functions, and backpropagation.",
  "citations": [
    {"section": "Chapter 3: Neural Networks", "url": "https://book.example.com/chapter-3"}
  ],
  "retrieved_chunks": [
    {
      "text": "Chapter 3 discusses the fundamentals of neural networks...",
      "metadata": {
        "url": "https://book.example.com/chapter-3",
        "section": "Chapter 3: Neural Networks",
        "chunk_id": "chunk-00042",
        "position": 2,
        "embedding_score": 0.8754
      }
    }
  ]
}
```

#### SessionCreateResponse

**Output from POST /sessions**

```python
from datetime import datetime

class SessionCreateResponse(BaseModel):
    session_id: str  # UUID
    created_at: datetime
```

#### SessionGetResponse

**Output from GET /sessions/{session_id}**

```python
class MessageView(BaseModel):
    role: str  # "user" or "assistant"
    content: str  # The message text
    created_at: datetime

class SessionGetResponse(BaseModel):
    session_id: str
    messages: List[MessageView]  # Ordered by created_at
```

#### HealthResponse

**Output from GET /health**

```python
class ServiceStatus(BaseModel):
    status: str  # "healthy" or "degraded"

class HealthResponse(BaseModel):
    status: str  # Overall status
    services: Dict[str, str]  # {"qdrant": "ok", "database": "ok", "openrouter": "ok"}
```

---

## Data Flow

### User Query Flow

```
1. User sends: POST /chat { "question": "What is AI?", "session_id": "...", "selected_text": null }

2. FastAPI route handler receives ChatRequest

3. BookRAGAgent executes:
   a. SelectionModeSubAgent: Check if selected_text present; if yes, override retrieval mode
   b. RetrievalSubAgent + VectorSearchSkill: Query Qdrant → get RetrievedChunks
   c. GuardrailsSubAgent + RetrievalValidationSkill: Validate chunks not empty
   d. AnswerSubAgent + GroundedSynthesisSkill: Call OpenRouter LLM → synthesize answer from chunks
   e. GuardrailsSubAgent + AntiHallucinationSkill: Validate answer is grounded; if not, return fallback
   f. MemorySubAgent + SessionPersistenceSkill: Store user message + assistant response in DB

4. Return ChatResponse { "answer": "...", "citations": [...], "retrieved_chunks": [...] }

5. Response stored in Session via ChatMessage table:
   - message_id: generated UUID
   - session_id: from request
   - role: "user" (for input), then "assistant" (for response)
   - content: the question, then the response JSON
   - metadata: chunks_used, latency, etc.
   - created_at: auto-timestamped
```

### Multi-Turn Flow

```
1. Request 1 (Q1): User asks first question
   → Agent processes, returns answer A1
   → Stored in Session: [Message(user, Q1), Message(assistant, A1)]

2. Request 2 (Q2): Same user, same session, asks follow-up
   → MemorySubAgent reads last 5 messages: [Q1, A1]
   → LLM prompt includes context: "Previous: User asked 'Q1', you answered 'A1'"
   → RetrievalSubAgent still only searches book chunks (NOT prior messages)
   → Agent synthesizes answer A2 using fresh chunks
   → Stored: [Message(user, Q1), Message(assistant, A1), Message(user, Q2), Message(assistant, A2)]

3. MemorySubAgent ensures context helps without contaminating retrieval
```

---

## Database Schema (SQL)

### DDL Statements

```sql
-- Create UUID extension (if not exists)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Sessions table
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB NULL,
    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_updated_at ON sessions(updated_at);

-- Chat messages table
CREATE TABLE chat_messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_chat_messages_session FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_session_created ON chat_messages(session_id, created_at);

-- Migration: Add trigger to update session.updated_at on new message
CREATE OR REPLACE FUNCTION update_session_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sessions SET updated_at = NOW() WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_update_session_on_message
AFTER INSERT ON chat_messages
FOR EACH ROW
EXECUTE FUNCTION update_session_updated_at();
```

---

## Validation Rules

### User

- `user_id`: Must be valid UUID
- `created_at`: Auto-set to current timestamp

### Session

- `session_id`: Must be unique UUID
- `user_id`: Must reference existing user_id; cannot be NULL
- `created_at`: Auto-set; immutable
- `updated_at`: Auto-set; updates on each new message
- `metadata`: If provided, must be valid JSON

### ChatMessage

- `message_id`: Must be unique UUID
- `session_id`: Must reference existing session; cannot be NULL
- `role`: Must be 'user' or 'assistant'
- `content`: Cannot be empty; max 8000 characters (for safety)
- `metadata`: If provided, must be valid JSON
- `created_at`: Auto-set; immutable

---

## Assumptions & Constraints

- **Single-user per session**: One session = one user at one time
- **Immutable messages**: Once created, messages are not updated or deleted (audit trail)
- **Session retention**: 90 days default (older sessions may be archived/deleted)
- **Chunk storage**: Chunks NOT stored in DB (ephemeral, from Qdrant during request)
- **Timestamp precision**: TIMESTAMP (seconds); millisecond precision via metadata if needed
- **Scaling**: Neon PostgreSQL auto-scales; no sharding required for initial deployment

---

## Future Extensions

- **User Preferences**: Add `user_preferences` table (theme, model preference, etc.)
- **Message Edits**: Add `edited_at` and `edit_count` to chat_messages for user-correctable sessions
- **Feedback**: Add `user_feedback` table (was answer helpful? any issues?)
- **Analytics**: Add `analytics` materialized view for conversation metrics

---

**Next**: API contract definitions in `/contracts/` subdirectory
