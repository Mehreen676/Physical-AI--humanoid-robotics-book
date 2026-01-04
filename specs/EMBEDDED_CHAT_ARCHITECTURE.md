# Embedded Chat Interface - Architecture Sketch

High-level architecture for embedding the agentic RAG chatbot in the Docusaurus book.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     EMBEDDED CHAT ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────────┘

User browses book → Interacts with chat → Receives AI answer
                         ↓
              Frontend (Client-Side)
                         ↓
              Backend (Server-Side)
                         ↓
              AI Agent Processing
```

---

## High-Level Data Flow

### Flow 1: Full-Book Question

```
┌──────────────┐
│ User reads   │
│ book page    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Clicks chat  │
│ button       │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ Types question:      │
│ "What is ROS 2?"     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│ Frontend Component (ChatWidget.tsx)                  │
│ - Creates ChatRequest object                         │
│ - retrieval_mode = "normal"                          │
│ - selected_text = null                               │
└──────┬───────────────────────────────────────────────┘
       │
       │ POST /api/v1/chat
       │ {
       │   "session_id": "session-123",
       │   "question": "What is ROS 2?",
       │   "retrieval_mode": "normal",
       │   "selected_text": null
       │ }
       ▼
┌──────────────────────────────────────────────────────┐
│ Backend API (FastAPI routes.py)                      │
│ - Receives request                                   │
│ - Validates input                                    │
│ - Routes to agent                                    │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│ Retrieval Layer (retrieval/retriever.py)             │
│ - Embeds query: "What is ROS 2?"                     │
│ - Searches Qdrant (top_k=5, threshold=0.7)           │
│ - Returns relevant chunks                            │
└──────┬───────────────────────────────────────────────┘
       │
       │ [Chunk 1, Chunk 2, Chunk 3, ...]
       ▼
┌──────────────────────────────────────────────────────┐
│ Context Formatter (agent/context_formatter.py)       │
│ - Formats chunks with metadata                       │
│ - Creates agent context string                       │
└──────┬───────────────────────────────────────────────┘
       │
       │ Formatted context
       ▼
┌──────────────────────────────────────────────────────┐
│ ChatKit Agent (agent/chatkit_agent.py)               │
│ - Receives question + context                        │
│ - System instructions: strict grounding              │
│ - Calls OpenAI API (GPT-4)                           │
│ - Generates answer                                   │
└──────┬───────────────────────────────────────────────┘
       │
       │ AI-generated answer
       ▼
┌──────────────────────────────────────────────────────┐
│ Answer Generator (agent/answer_generator.py)         │
│ - Validates grounding                                │
│ - Detects refusals                                   │
│ - Extracts citations                                 │
└──────┬───────────────────────────────────────────────┘
       │
       │ Validated answer + citations
       ▼
┌──────────────────────────────────────────────────────┐
│ Database (storage/database.py)                       │
│ - Stores turn in session                             │
│ - Updates conversation history                       │
└──────┬───────────────────────────────────────────────┘
       │
       │ ChatResponse object
       │ {
       │   "session_id": "session-123",
       │   "answer": "ROS 2 is...",
       │   "citations": [...],
       │   "grounded": true
       │ }
       ▼
┌──────────────────────────────────────────────────────┐
│ Frontend API Client (apiClient.ts)                   │
│ - Receives response                                  │
│ - Parses JSON                                        │
│ - Updates component state                            │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│ Message Display (MessageList.tsx)                    │
│ - Renders answer with markdown                       │
│ - Shows expandable citations                         │
│ - Auto-scrolls to newest message                     │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ User reads   │
│ AI answer    │
└──────────────┘
```

### Flow 2: Selected-Text Question

```
┌──────────────┐
│ User reads   │
│ book page    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ Highlights text:         │
│ "DDS is used for         │
│  inter-node comms"       │
└──────┬───────────────────┘
       │
       │ Selection detected (selectionchange event)
       ▼
┌──────────────────────────────────────────────────────┐
│ ChatWidget State Update                              │
│ - selectedText = "DDS is used for inter-node comms"  │
│ - Badge appears in UI                                │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────┐
│ User opens chat      │
│ Types: "Explain this"│
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│ Frontend Component                                   │
│ - Creates ChatRequest                                │
│ - retrieval_mode = "selected_text"                   │
│ - selected_text = "DDS is used for inter-node comms" │
└──────┬───────────────────────────────────────────────┘
       │
       │ POST /api/v1/chat
       │ {
       │   "question": "Explain this",
       │   "retrieval_mode": "selected_text",
       │   "selected_text": "DDS is used for inter-node comms"
       │ }
       ▼
┌──────────────────────────────────────────────────────┐
│ Backend API                                          │
│ - Validates selected_text present                    │
│ - Routes to retrieval                                │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│ Retrieval Layer                                      │
│ - Embeds SELECTED TEXT (not query)                   │
│ - Searches Qdrant (top_k=3, threshold=0.85)          │
│ - Returns highly relevant chunks                     │
└──────┬───────────────────────────────────────────────┘
       │
       │ Constrained chunks
       ▼
┌──────────────────────────────────────────────────────┐
│ Selected Text Handler                                │
│ - Prepares context with selection highlighted        │
│ - Adds instruction: "Answer based on selection only" │
└──────┬───────────────────────────────────────────────┘
       │
       │ Selected-text context
       ▼
┌──────────────────────────────────────────────────────┐
│ ChatKit Agent                                        │
│ - Receives constrained context                       │
│ - Generates answer scoped to selection               │
└──────┬───────────────────────────────────────────────┘
       │
       │ Scoped answer
       ▼
┌──────────────────────────────────────────────────────┐
│ Response to Frontend                                 │
│ - Answer constrained to selected text                │
│ - Citations from relevant chunks                     │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────┐
│ User reads focused   │
│ answer about         │
│ selected passage     │
└──────────────────────┘
```

---

## Component Architecture

### Frontend Components (Client-Side)

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCUSAURUS PAGE                          │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Book Content (Markdown/MDX)                       │    │
│  │  - Introduction                                    │    │
│  │  - Chapter 1: ROS 2 Overview                       │    │
│  │  - Chapter 2: DDS Communication                    │    │
│  │  ...                                               │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┤
│  │                ROOT.JS (Theme Wrapper)                  │
│  │  - Wraps all pages                                      │
│  │  - Renders <ChatWidget />                               │
│  └─────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┤
│  │              CHAT WIDGET COMPONENT                      │
│  │                                                         │
│  │  ┌───────────────────────────────────────────────┐     │
│  │  │  ChatButton (Floating)                        │     │
│  │  │  - Bottom-right position                      │     │
│  │  │  - Toggle chat panel                          │     │
│  │  │  - Visual indicator (unread badge)            │     │
│  │  └───────────────────────────────────────────────┘     │
│  │                                                         │
│  │  ┌───────────────────────────────────────────────┐     │
│  │  │  ChatPanel (Collapsible)                      │     │
│  │  │                                               │     │
│  │  │  ┌─────────────────────────────────────┐      │     │
│  │  │  │  ChatHeader                        │      │     │
│  │  │  │  - Title: "Book Assistant"         │      │     │
│  │  │  │  - Close button                    │      │     │
│  │  │  └─────────────────────────────────────┘      │     │
│  │  │                                               │     │
│  │  │  ┌─────────────────────────────────────┐      │     │
│  │  │  │  SelectedTextBadge (Conditional)   │      │     │
│  │  │  │  - Shows selected text              │      │     │
│  │  │  │  - Clear button                     │      │     │
│  │  │  └─────────────────────────────────────┘      │     │
│  │  │                                               │     │
│  │  │  ┌─────────────────────────────────────┐      │     │
│  │  │  │  MessageList (Scrollable)          │      │     │
│  │  │  │                                    │      │     │
│  │  │  │  ┌─────────────────────────┐       │      │     │
│  │  │  │  │ UserMessage (right)     │       │      │     │
│  │  │  │  │ "What is ROS 2?"        │       │      │     │
│  │  │  │  └─────────────────────────┘       │      │     │
│  │  │  │                                    │      │     │
│  │  │  │  ┌─────────────────────────┐       │      │     │
│  │  │  │  │ AssistantMessage (left) │       │      │     │
│  │  │  │  │ "ROS 2 is..."           │       │      │     │
│  │  │  │  │ ▼ Sources (3)            │       │      │     │
│  │  │  │  └─────────────────────────┘       │      │     │
│  │  │  │                                    │      │     │
│  │  │  │  ┌─────────────────────────┐       │      │     │
│  │  │  │  │ LoadingIndicator        │       │      │     │
│  │  │  │  │ ● ● ● (animated)        │       │      │     │
│  │  │  │  └─────────────────────────┘       │      │     │
│  │  │  │                                    │      │     │
│  │  │  └─────────────────────────────────────┘      │     │
│  │  │                                               │     │
│  │  │  ┌─────────────────────────────────────┐      │     │
│  │  │  │  ErrorMessage (Conditional)         │      │     │
│  │  │  │  - Error text                       │      │     │
│  │  │  │  - Retry button                     │      │     │
│  │  │  └─────────────────────────────────────┘      │     │
│  │  │                                               │     │
│  │  │  ┌─────────────────────────────────────┐      │     │
│  │  │  │  MessageInput                       │      │     │
│  │  │  │  ┌────────────────────┬──────┐      │      │     │
│  │  │  │  │ Textarea           │ Send │      │      │     │
│  │  │  │  │ (auto-resize)      │  ▶  │      │      │     │
│  │  │  │  └────────────────────┴──────┘      │      │     │
│  │  │  └─────────────────────────────────────┘      │     │
│  │  │                                               │     │
│  │  └───────────────────────────────────────────────┘     │
│  │                                                         │
│  └─────────────────────────────────────────────────────────┤
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Frontend State Management

```
┌────────────────────────────────────────┐
│     ChatWidget Component State        │
├────────────────────────────────────────┤
│ isOpen: boolean                        │
│ - Tracks panel open/close              │
│ - Persisted in sessionStorage          │
├────────────────────────────────────────┤
│ messages: Message[]                    │
│ - Array of user + assistant messages   │
│ - Rendered in MessageList              │
├────────────────────────────────────────┤
│ isLoading: boolean                     │
│ - True while waiting for API response  │
│ - Shows loading indicator              │
├────────────────────────────────────────┤
│ error: string | null                   │
│ - Error message if request fails       │
│ - Shows error UI with retry button     │
├────────────────────────────────────────┤
│ selectedText: string | null            │
│ - Text user highlighted on page        │
│ - Auto-detected via selectionchange    │
│ - Cleared after sending question       │
├────────────────────────────────────────┤
│ sessionId: string | null               │
│ - UUID-like session identifier         │
│ - Generated on first interaction       │
│ - Stored in sessionStorage             │
│ - Sent with all API requests           │
└────────────────────────────────────────┘
```

### Backend Architecture (Server-Side)

```
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  API Layer (api/routes.py)                                  │
│  - POST /api/v1/chat                                        │
│  - POST /api/v1/sessions                                    │
│  - GET /api/v1/sessions/{id}                                │
│  - GET /api/v1/health                                       │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Request Validation                                         │
│  - Pydantic schema validation                               │
│  - Input sanitization                                       │
│  - Max length checks                                        │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Retrieval Layer (retrieval/)                               │
│                                                             │
│  ┌────────────────────────────────────────────┐            │
│  │  SemanticRetriever                         │            │
│  │  - retrieve(query, mode, selected_text)    │            │
│  └────────┬───────────────────────────────────┘            │
│           │                                                 │
│           ├──► Normal Mode                                 │
│           │    - Embed query                               │
│           │    - Search Qdrant (k=5, t=0.7)                │
│           │                                                 │
│           └──► Selected-Text Mode                          │
│                - Embed selected_text                        │
│                - Search Qdrant (k=3, t=0.85)               │
│                                                             │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Retrieved chunks
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent Layer (agent/)                                       │
│                                                             │
│  ┌────────────────────────────────────────────┐            │
│  │  ContextFormatter                          │            │
│  │  - format_chunks(chunks)                   │            │
│  │  - Adds chapter/section metadata           │            │
│  └────────┬───────────────────────────────────┘            │
│           │                                                 │
│           │ Formatted context                              │
│           ▼                                                 │
│  ┌────────────────────────────────────────────┐            │
│  │  ChatKitAgent                              │            │
│  │  - create_chat_completion()                │            │
│  │  - System instructions: strict grounding   │            │
│  │  - Temperature = 0 (deterministic)         │            │
│  │  - Calls OpenAI API                        │            │
│  └────────┬───────────────────────────────────┘            │
│           │                                                 │
│           │ AI-generated answer                            │
│           ▼                                                 │
│  ┌────────────────────────────────────────────┐            │
│  │  AnswerGenerator                           │            │
│  │  - generate_answer()                       │            │
│  │  - validate_grounding()                    │            │
│  │  - detect refusals                         │            │
│  │  - extract_citations()                     │            │
│  └────────┬───────────────────────────────────┘            │
│                                                             │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Validated answer + citations
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Storage Layer (storage/)                                   │
│                                                             │
│  ┌────────────────────────────────────────────┐            │
│  │  Database (SQLite / Neon Postgres)         │            │
│  │  - create_session()                        │            │
│  │  - add_turn()                              │            │
│  │  - get_conversation_history()              │            │
│  └────────────────────────────────────────────┘            │
│                                                             │
└────────────┬────────────────────────────────────────────────┘
             │
             │ ChatResponse object
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Response Serialization                                     │
│  - Pydantic model → JSON                                    │
│  - Include: answer, citations, metadata                     │
└────────────┬────────────────────────────────────────────────┘
             │
             │ HTTP 200 OK
             ▼
         Frontend
```

---

## Network Communication

### API Contract

```
┌─────────────────────────────────────────────────────────────┐
│                  REQUEST (Frontend → Backend)               │
└─────────────────────────────────────────────────────────────┘

POST /api/v1/chat
Content-Type: application/json

{
  "session_id": "session-1704268800000-abc123",  // Optional on first request
  "question": "What is ROS 2?",                   // Required, max 1000 chars
  "retrieval_mode": "normal",                     // "normal" | "selected_text"
  "selected_text": null                           // Required if mode = "selected_text"
}

┌─────────────────────────────────────────────────────────────┐
│                  RESPONSE (Backend → Frontend)              │
└─────────────────────────────────────────────────────────────┘

HTTP/1.1 200 OK
Content-Type: application/json

{
  "session_id": "session-1704268800000-abc123",  // Same or new if not provided
  "answer": "ROS 2 is the next generation of the Robot Operating System... [Chapter 1, Section 1.2]",
  "citations": [
    {
      "chapter": "Chapter 1",
      "section": "Section 1.2",
      "text_snippet": "ROS 2 is the next generation of the Robot Operating System, designed to address...",
      "score": 0.85
    },
    {
      "chapter": "Chapter 2",
      "section": "Section 2.1",
      "text_snippet": "Key improvements in ROS 2 include...",
      "score": 0.78
    }
  ],
  "retrieval_mode": "normal",
  "grounded": true,
  "metadata": {
    "latency_ms": 2345.67,
    "num_chunks": 5,
    "is_refusal": false
  }
}
```

### Error Responses

```
┌─────────────────────────────────────────────────────────────┐
│              ERROR RESPONSES (Backend → Frontend)           │
└─────────────────────────────────────────────────────────────┘

// 400 Bad Request - Invalid input
{
  "detail": "Question is required and cannot be empty"
}

// 404 Not Found - Session not found
{
  "detail": "Session not found: session-xyz"
}

// 500 Internal Server Error - Backend failure
{
  "detail": "Internal server error"
}

// Network Error (Frontend-detected)
{
  "error": "Unable to connect to chatbot. Please check your connection."
}

// Timeout Error (Frontend-detected)
{
  "error": "Request timed out. Please try again."
}
```

---

## Deployment Architecture

### Development Environment

```
┌────────────────────────────────────────────────────────────┐
│                   DEVELOPMENT SETUP                        │
└────────────────────────────────────────────────────────────┘

Developer Machine
├─ Terminal 1: Frontend
│  └─ cd front-end
│     npm start
│     → http://localhost:3000
│
└─ Terminal 2: Backend
   └─ cd backend_v3
      python main.py
      → http://localhost:8000

┌────────────────────────────────────────────────────────────┐
│ Configuration                                              │
├────────────────────────────────────────────────────────────┤
│ Frontend .env:                                             │
│   CHATBOT_BACKEND_URL=http://localhost:8000                │
│                                                            │
│ Backend .env:                                              │
│   OPENAI_API_KEY=sk-...                                    │
│   QDRANT_URL=https://...                                   │
│   QDRANT_API_KEY=...                                       │
│   DATABASE_URL=                  (uses SQLite)             │
│   CORS_ORIGINS=http://localhost:3000                       │
└────────────────────────────────────────────────────────────┘
```

### Production Environment

```
┌────────────────────────────────────────────────────────────┐
│                  PRODUCTION DEPLOYMENT                     │
└────────────────────────────────────────────────────────────┘

User Browser
    │
    │ HTTPS
    ▼
┌────────────────────────────────────────┐
│  GitHub Pages                          │
│  https://mehreen676.github.io/         │
│  Physical-AI--humanoid-robotics-book/  │
│                                        │
│  - Static HTML/CSS/JS                  │
│  - Docusaurus-generated                │
│  - Chat widget embedded                │
└────────────┬───────────────────────────┘
             │
             │ HTTPS POST /api/v1/chat
             │
             ▼
┌────────────────────────────────────────┐
│  Railway / Render                      │
│  https://your-backend.railway.app      │
│                                        │
│  - FastAPI backend                     │
│  - Agentic RAG (backend_v3)            │
│  - Environment variables set           │
└────────────┬───────────────────────────┘
             │
             ├──► Qdrant Cloud
             │    - Vector database
             │    - Book embeddings
             │
             ├──► OpenAI API
             │    - GPT-4 Turbo
             │    - ChatKit agent
             │
             └──► Neon Postgres
                  - Session storage
                  - Conversation history

┌────────────────────────────────────────────────────────────┐
│ Configuration                                              │
├────────────────────────────────────────────────────────────┤
│ GitHub Secrets (frontend):                                 │
│   CHATBOT_BACKEND_URL=https://your-backend.railway.app     │
│                                                            │
│ Railway Environment (backend):                             │
│   OPENAI_API_KEY=sk-...                                    │
│   QDRANT_URL=https://...                                   │
│   QDRANT_API_KEY=...                                       │
│   DATABASE_URL=postgresql://...@neon.tech/...             │
│   CORS_ORIGINS=https://mehreen676.github.io                │
└────────────────────────────────────────────────────────────┘
```

---

## Performance Characteristics

### Frontend Performance

```
┌────────────────────────────────────────────────────────────┐
│                  FRONTEND METRICS                          │
├────────────────────────────────────────────────────────────┤
│ Bundle Size                                                │
│ - Chat widget: ~15KB (gzipped)                             │
│ - react-markdown: ~25KB (gzipped)                          │
│ - Total added: ~40KB                                       │
│ - Target: <50KB ✅                                          │
├────────────────────────────────────────────────────────────┤
│ Load Time                                                  │
│ - Widget initialization: <100ms                            │
│ - No impact on page load (lazy component)                  │
│ - First render: <50ms                                      │
├────────────────────────────────────────────────────────────┤
│ Runtime Performance                                        │
│ - Text selection detection: <10ms                          │
│ - Message rendering: <20ms                                 │
│ - State updates: <5ms                                      │
│ - Auto-scroll: <10ms                                       │
└────────────────────────────────────────────────────────────┘
```

### Backend Performance

```
┌────────────────────────────────────────────────────────────┐
│                  BACKEND LATENCY (P95)                     │
├────────────────────────────────────────────────────────────┤
│ API Request Validation: ~10ms                              │
│ Retrieval (Qdrant + embeddings): ~500ms                    │
│ Context Formatting: ~40ms                                  │
│ ChatKit Agent (OpenAI API): ~2500ms                        │
│ Answer Validation: ~50ms                                   │
│ Citation Extraction: ~30ms                                 │
│ Database Storage: ~200ms                                   │
├────────────────────────────────────────────────────────────┤
│ Total End-to-End: ~3.3 seconds                             │
│ Target: <5 seconds ✅                                       │
└────────────────────────────────────────────────────────────┘
```

### Network Performance

```
┌────────────────────────────────────────────────────────────┐
│                  NETWORK CHARACTERISTICS                   │
├────────────────────────────────────────────────────────────┤
│ Request Size                                               │
│ - Typical question: ~200 bytes                             │
│ - With selected text (max): ~2.5KB                         │
│ - Headers + session: ~500 bytes                            │
├────────────────────────────────────────────────────────────┤
│ Response Size                                              │
│ - Answer (typical): ~500 bytes                             │
│ - Citations (3-5): ~1KB                                    │
│ - Metadata: ~200 bytes                                     │
│ - Total: ~1.7KB                                            │
├────────────────────────────────────────────────────────────┤
│ Timeouts                                                   │
│ - Frontend timeout: 30 seconds                             │
│ - Backend processing: No hard limit                        │
│ - Recommended: <10 seconds for UX                          │
└────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Frontend Security

```
┌────────────────────────────────────────────────────────────┐
│              FRONTEND SECURITY BOUNDARIES                  │
├────────────────────────────────────────────────────────────┤
│ NO Secrets in Frontend                                     │
│ ❌ No OPENAI_API_KEY                                        │
│ ❌ No QDRANT_API_KEY                                        │
│ ❌ No DATABASE_URL                                          │
│ ✅ Only backend URL (public)                                │
├────────────────────────────────────────────────────────────┤
│ Input Sanitization                                         │
│ - Max question length: 1000 characters                     │
│ - Max selected text: 2000 characters                       │
│ - No HTML injection (React escapes)                        │
│ - No SQL injection (backend validates)                     │
├────────────────────────────────────────────────────────────┤
│ Output Sanitization                                        │
│ - ReactMarkdown: XSS prevention built-in                   │
│ - No dangerouslySetInnerHTML                               │
│ - All user content escaped                                 │
├────────────────────────────────────────────────────────────┤
│ Session Security                                           │
│ - Session ID non-guessable (timestamp + random)            │
│ - Stored in sessionStorage (not localStorage)              │
│ - No personal information collected                        │
│ - No tracking or analytics                                 │
└────────────────────────────────────────────────────────────┘
```

### Backend Security

```
┌────────────────────────────────────────────────────────────┐
│              BACKEND SECURITY BOUNDARIES                   │
├────────────────────────────────────────────────────────────┤
│ CORS Configuration                                         │
│ - Allowed origins: GitHub Pages + localhost                │
│ - No wildcard (*) in production                            │
│ - Credentials: false (no cookies)                          │
├────────────────────────────────────────────────────────────┤
│ Environment Variables                                      │
│ - All secrets in .env                                      │
│ - Never committed to git                                   │
│ - Loaded via python-dotenv                                 │
├────────────────────────────────────────────────────────────┤
│ Input Validation                                           │
│ - Pydantic schema enforcement                              │
│ - Type checking                                            │
│ - Length limits                                            │
│ - SQL injection prevention (ORM)                           │
├────────────────────────────────────────────────────────────┤
│ Rate Limiting (Optional - Future)                          │
│ - Per IP: 60 requests/minute                               │
│ - Per session: 30 requests/minute                          │
│ - Prevents abuse                                           │
└────────────────────────────────────────────────────────────┘
```

---

## Error Handling Architecture

### Frontend Error States

```
┌────────────────────────────────────────────────────────────┐
│              FRONTEND ERROR HANDLING                       │
├────────────────────────────────────────────────────────────┤
│ Network Error                                              │
│ - Cause: No internet, CORS failure                         │
│ - Display: "Unable to connect to chatbot"                  │
│ - Action: Retry button                                     │
├────────────────────────────────────────────────────────────┤
│ Timeout Error                                              │
│ - Cause: Response >30 seconds                              │
│ - Display: "Request timed out"                             │
│ - Action: Retry button                                     │
├────────────────────────────────────────────────────────────┤
│ HTTP Error (4xx/5xx)                                       │
│ - Cause: Backend error                                     │
│ - Display: "Something went wrong. Please try again."       │
│ - Action: Retry button                                     │
├────────────────────────────────────────────────────────────┤
│ Validation Error                                           │
│ - Cause: Empty question, invalid input                     │
│ - Display: Disable send button                             │
│ - Action: No retry (fix input)                             │
└────────────────────────────────────────────────────────────┘
```

### Backend Error Handling

```
┌────────────────────────────────────────────────────────────┐
│              BACKEND ERROR HANDLING                        │
├────────────────────────────────────────────────────────────┤
│ Validation Error (400)                                     │
│ - Return: {"detail": "Question is required"}               │
│ - Log: WARNING level                                       │
│ - No retry on frontend                                     │
├────────────────────────────────────────────────────────────┤
│ Retrieval Error (500)                                      │
│ - Cause: Qdrant down, embedding failure                    │
│ - Fallback: Return refusal message                         │
│ - Log: ERROR level                                         │
│ - Frontend: Show retry                                     │
├────────────────────────────────────────────────────────────┤
│ Agent Error (500)                                          │
│ - Cause: OpenAI API failure                                │
│ - Fallback: Return error message                           │
│ - Log: ERROR level with details                            │
│ - Frontend: Show retry                                     │
├────────────────────────────────────────────────────────────┤
│ Database Error (Non-blocking)                              │
│ - Cause: Neon Postgres down                                │
│ - Behavior: Answer still returned                          │
│ - Log: WARNING level                                       │
│ - Impact: History not saved                                │
└────────────────────────────────────────────────────────────┘
```

---

## Monitoring and Observability

### Logging Strategy

```
┌────────────────────────────────────────────────────────────┐
│                    LOGGING ARCHITECTURE                    │
├────────────────────────────────────────────────────────────┤
│ Frontend Logging                                           │
│ - Browser console.error() for errors                       │
│ - No analytics or tracking                                 │
│ - User privacy preserved                                   │
├────────────────────────────────────────────────────────────┤
│ Backend Logging (Structured JSON)                          │
│ {                                                          │
│   "timestamp": "2026-01-03T12:34:56Z",                     │
│   "level": "INFO",                                         │
│   "event": "chat_request",                                 │
│   "session_id": "session-123",                             │
│   "retrieval_mode": "normal",                              │
│   "latency_ms": 2345.67,                                   │
│   "num_chunks": 5,                                         │
│   "is_refusal": false                                      │
│ }                                                          │
├────────────────────────────────────────────────────────────┤
│ Log Levels                                                 │
│ - DEBUG: Detailed diagnostic info                          │
│ - INFO: Request/response flow                              │
│ - WARNING: Recoverable errors                              │
│ - ERROR: Unrecoverable errors                              │
└────────────────────────────────────────────────────────────┘
```

---

## **Architecture Summary**

```
User ──► Book Page ──► Chat Widget ──► API Client ──► FastAPI
                                                         │
                                    ┌────────────────────┤
                                    │                    │
                              Retrieval ◄──► Qdrant      │
                                    │                    │
                              Agent ◄──► OpenAI          │
                                    │                    │
                              Database ◄──► Neon         │
                                    │                    │
                                    └────────────────────┤
                                                         │
User ◄── Answer Display ◄── JSON Response ◄──────────────┘
```

**Key Principles**:
1. **Thin frontend** - Only UI, state, and API calls
2. **Thick backend** - All AI, retrieval, and logic
3. **Clear separation** - Frontend never sees API keys
4. **Secure by default** - CORS, HTTPS, input validation
5. **Graceful degradation** - Errors don't break UI
6. **Performance-first** - <50KB bundle, <5s responses

---

**Document Version**: 1.0.0
**Last Updated**: 2026-01-03
**Status**: Complete architecture specification
