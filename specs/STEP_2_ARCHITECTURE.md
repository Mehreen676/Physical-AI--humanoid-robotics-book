# Step 2: RAG Agent Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                              │
│                        (Frontend - Docusaurus Site)                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/REST
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI REST API                              │
│                          (api/routes.py)                                 │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ POST /chat  │  │POST /sessions│ │GET /sessions │ │ GET /health │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                                          │
│              Middleware: CORS, Logging, Error Handling                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           BOOK RAG AGENT                                 │
│                         (agent/agent.py)                                 │
│                                                                          │
│                    Main Orchestrator - Coordinates:                      │
│            1. Memory → 2. Retrieval → 3. Answer → 4. Guardrails        │
└─────────────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Memory     │ │  Retrieval   │ │   Answer     │ │ Guardrails   │
│  SubAgent    │ │  SubAgent    │ │  SubAgent    │ │  SubAgent    │
│              │ │              │ │              │ │              │
│ • Load       │ │ • Embed      │ │ • Construct  │ │ • Validate   │
│   history    │ │   query      │ │   RAG prompt │ │   grounding  │
│ • Format     │ │ • Search     │ │ • Call LLM   │ │ • Detect     │
│   messages   │ │   Qdrant     │ │ • Extract    │ │   hallucin.  │
│ • Limit 10   │ │ • Filter     │ │   citations  │ │ • Reject if  │
│              │ │   results    │ │              │ │   unsafe     │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
         │              │              │              │
         │              │              ▼              │
         │              │     ┌──────────────┐       │
         │              │     │   OpenRouter │       │
         │              │     │  Claude 3.5  │       │
         │              │     │   Sonnet     │       │
         │              │     └──────────────┘       │
         │              │                             │
         │              ▼                             │
         │     ┌──────────────┐                      │
         │     │   Gemini     │                      │
         │     │  Embeddings  │                      │
         │     │  (768-dim)   │                      │
         │     └──────────────┘                      │
         │              │                             │
         │              ▼                             │
         │     ┌──────────────┐                      │
         │     │   Qdrant     │                      │
         │     │  Vector DB   │                      │
         │     │  (Cosine)    │                      │
         │     └──────────────┘                      │
         │                                            │
         ▼                                            ▼
┌──────────────────────────────────────────────────────────┐
│              POSTGRESQL DATABASE                         │
│              (storage/sessions.py)                       │
│                                                           │
│  ┌──────────────┐           ┌──────────────┐            │
│  │   sessions   │           │   messages   │            │
│  │              │           │              │            │
│  │ • id (UUID)  │  1:N      │ • id (serial)│            │
│  │ • created_at │◀─────────▶│ • session_id │            │
│  │ • updated_at │           │ • role       │            │
│  │              │           │ • content    │            │
│  │              │           │ • timestamp  │            │
│  └──────────────┘           └──────────────┘            │
└──────────────────────────────────────────────────────────┘
```

---

## Request Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER SENDS QUESTION                          │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ POST /chat
                             │ {
                             │   session_id: "uuid",
                             │   question: "What is ROS 2?",
                             │   retrieval_mode: "normal"
                             │ }
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI ENDPOINT                             │
│                     api/routes.py                                │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ Validate request
                             │ Log incoming request
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BOOK RAG AGENT                                │
│                    agent.chat()                                  │
└─────────────────────────────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  STEP 1: MEMORY  │ │ STEP 2: RETRIEVAL│ │ STEP 3: ANSWER   │
│                  │ │                  │ │                  │
│ MemorySubAgent   │ │ RetrievalSubAgent│ │ AnswerSubAgent   │
│                  │ │                  │ │                  │
│ 1. Load session  │ │ 1. Detect mode   │ │ 1. Construct     │
│    from DB       │ │    (normal vs    │ │    RAG prompt    │
│                  │ │    selected text)│ │                  │
│ 2. Get last 10   │ │                  │ │ 2. Include:      │
│    messages      │ │ 2. Embed query   │ │    • Question    │
│                  │ │    (Gemini)      │ │    • Chunks      │
│ 3. Format for    │ │                  │ │    • History     │
│    LLM context   │ │ 3. Search Qdrant │ │                  │
│                  │ │    • top_k=5     │ │ 3. Call Claude   │
│ Return:          │ │    • threshold   │ │    via OpenRouter│
│ [                │ │      =0.7        │ │                  │
│   {role: "user", │ │                  │ │ 4. Parse:        │
│    content: "Q1"}│ │ 4. Filter by     │ │    • Answer text │
│   {role: "asst", │ │    score         │ │    • Citations   │
│    content: "A1"}│ │                  │ │                  │
│   ...            │ │ Return:          │ │ Return:          │
│ ]                │ │ [                │ │ {                │
│                  │ │   {              │ │   answer: "ROS 2 │
│                  │ │     text: "...", │ │   is...",        │
│                  │ │     metadata: {  │ │   citations: [   │
│                  │ │       chapter,   │ │     {chapter,    │
│                  │ │       section    │ │      section}    │
│                  │ │     }            │ │   ]              │
│                  │ │   }              │ │ }                │
│                  │ │ ]                │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ STEP 4: VALIDATE │
                    │                  │
                    │ GuardrailsSubAgent│
                    │                  │
                    │ 1. Check if answer│
                    │    is grounded in│
                    │    retrieved     │
                    │    chunks        │
                    │                  │
                    │ 2. Detect        │
                    │    hallucination │
                    │    patterns      │
                    │                  │
                    │ 3. Validate      │
                    │    citation      │
                    │    accuracy      │
                    │                  │
                    │ Return:          │
                    │ {                │
                    │   is_valid: true,│
                    │   reason: ""     │
                    │ }                │
                    └──────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ STEP 5: PERSIST  │
                    │                  │
                    │ Save to Database │
                    │                  │
                    │ 1. Save user     │
                    │    question      │
                    │                  │
                    │ 2. Save assistant│
                    │    answer        │
                    │                  │
                    │ 3. Update session│
                    │    timestamp     │
                    └──────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     RETURN TO USER                               │
│                                                                  │
│ {                                                                │
│   answer: "ROS 2 (Robot Operating System 2) is...",            │
│   citations: [                                                   │
│     {                                                            │
│       section: "Introduction to ROS 2",                         │
│       chapter: "Getting Started",                               │
│       url: "/docs/getting-started/intro-ros2"                   │
│     }                                                            │
│   ],                                                             │
│   sources: ["Getting Started > Introduction to ROS 2"],         │
│   metadata: {                                                    │
│     chunks_retrieved: 3,                                         │
│     model_used: "claude-3-5-sonnet",                            │
│     latency_ms: 1450                                             │
│   }                                                              │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Interaction Matrix

| Component | Depends On | Provides To | Purpose |
|-----------|-----------|-------------|---------|
| **FastAPI App** (main.py) | All routes, middleware | External clients | HTTP server, request routing |
| **API Routes** (api/routes.py) | BookRAGAgent, storage | FastAPI app | Endpoint handlers |
| **BookRAGAgent** (agent/agent.py) | All sub-agents, storage | API routes | Main orchestrator |
| **MemorySubAgent** | storage/sessions | BookRAGAgent | Conversation history |
| **RetrievalSubAgent** | Gemini, Qdrant | BookRAGAgent | Relevant chunks |
| **AnswerSubAgent** | OpenRouter/Claude | BookRAGAgent | Generated answers |
| **GuardrailsSubAgent** | - | BookRAGAgent | Answer validation |
| **GeminiEmbeddings** | Gemini API | RetrievalSubAgent | Query vectors |
| **QdrantRetriever** | Qdrant API | RetrievalSubAgent | Vector search |
| **OpenRouterClient** | OpenRouter API | AnswerSubAgent | LLM generation |
| **Session Storage** | PostgreSQL | MemorySubAgent, routes | Data persistence |

---

## Database Schema

```sql
-- sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- messages table
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- indexes for performance
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);

-- Example data
-- Session: 123e4567-e89b-12d3-a456-426614174000
-- Messages:
--   1. user: "What is ROS 2?"
--   2. assistant: "ROS 2 is..."
--   3. user: "How do I install it?"
--   4. assistant: "To install ROS 2..."
```

---

## Data Models (Pydantic Schemas)

```python
# Request Models
class ChatRequest(BaseModel):
    session_id: str
    question: str
    retrieval_mode: Literal["normal", "selected_text"] = "normal"
    selected_text: Optional[str] = None

# Response Models
class Citation(BaseModel):
    section: str
    chapter: str
    url: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    sources: List[str]
    metadata: Dict[str, Any]

class SessionResponse(BaseModel):
    session_id: str
    created_at: datetime
    messages: List[Dict[str, str]]

class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    services: Dict[str, str]
    timestamp: datetime
```

---

## Error Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     ERROR SCENARIOS                              │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│ User sends       │
│ invalid request  │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ FastAPI          │
│ Pydantic         │
│ validation fails │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Return 422       │
│ Validation error │
└──────────────────┘


┌──────────────────┐
│ Gemini API       │
│ quota exceeded   │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ RetrievalSubAgent│
│ catches exception│
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Fallback to      │
│ MockEmbeddings   │
│ (if configured)  │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Continue with    │
│ degraded mode    │
└──────────────────┘


┌──────────────────┐
│ Qdrant           │
│ connection fails │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ RetrievalSubAgent│
│ retries 3x with  │
│ exponential      │
│ backoff          │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ All retries fail │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Return error:    │
│ "Unable to       │
│ retrieve context"│
└──────────────────┘


┌──────────────────┐
│ OpenRouter       │
│ rate limit       │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ AnswerSubAgent   │
│ exponential      │
│ backoff (5x)     │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Return 503       │
│ Service          │
│ Unavailable      │
└──────────────────┘


┌──────────────────┐
│ Guardrails detect│
│ hallucination    │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ GuardrailsSubAgent│
│ marks as invalid │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Return to user:  │
│ "I don't have    │
│ enough info"     │
└──────────────────┘
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RENDER PLATFORM                           │
│                        (PaaS Hosting)                            │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Docker Container │ │  Neon PostgreSQL │ │ Qdrant Cloud     │
│                  │ │  (Serverless)    │ │ (Vector DB)      │
│ • FastAPI app    │ │                  │ │                  │
│ • Uvicorn server │ │ • Sessions table │ │ • book-chunks    │
│ • Port 10000     │ │ • Messages table │ │   collection     │
│                  │ │                  │ │ • 768-dim vectors│
│ Health check:    │ │ Connection pool  │ │ • Cosine distance│
│ GET /health      │ │ (max 10)         │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             │ Environment Variables:
                             │ • DATABASE_URL
                             │ • QDRANT_URL
                             │ • QDRANT_API_KEY
                             │ • GEMINI_API_KEY
                             │ • OPENROUTER_API_KEY
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                            │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │  Gemini API    │  │  OpenRouter    │  │  Neon DB       │   │
│  │  (Embeddings)  │  │  (Claude 3.5)  │  │  (PostgreSQL)  │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SECURITY LAYERS                           │
└─────────────────────────────────────────────────────────────────┘

1. TRANSPORT LAYER
   ┌──────────────────────────────────────┐
   │ • HTTPS only (TLS 1.3)               │
   │ • No HTTP fallback                   │
   │ • Certificate validation             │
   └──────────────────────────────────────┘

2. APPLICATION LAYER
   ┌──────────────────────────────────────┐
   │ • CORS whitelist (frontend origin)   │
   │ • Request validation (Pydantic)      │
   │ • SQL injection prevention (ORM)     │
   │ • XSS sanitization (response escaping│
   └──────────────────────────────────────┘

3. API KEY MANAGEMENT
   ┌──────────────────────────────────────┐
   │ • Environment variables only         │
   │ • Never committed to git             │
   │ • Masked in logs                     │
   │ • Rotated regularly (manual)         │
   └──────────────────────────────────────┘

4. DATABASE SECURITY
   ┌──────────────────────────────────────┐
   │ • Encrypted at rest (Neon default)   │
   │ • SSL/TLS connections only           │
   │ • Least privilege DB user            │
   │ • Connection pooling limits          │
   └──────────────────────────────────────┘

5. DOCKER SECURITY
   ┌──────────────────────────────────────┐
   │ • Non-root user (appuser)            │
   │ • Minimal base image (python:slim)   │
   │ • No secrets in Dockerfile           │
   │ • Read-only filesystem (optional)    │
   └──────────────────────────────────────┘

6. CONTENT SECURITY
   ┌──────────────────────────────────────┐
   │ • Hallucination detection            │
   │ • Answer grounding validation        │
   │ • Citation verification              │
   │ • Prompt injection prevention        │
   └──────────────────────────────────────┘
```

---

## Performance Optimization Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE TARGETS                           │
└─────────────────────────────────────────────────────────────────┘

Target Latency (P95): < 2 seconds
Target Throughput: 100 req/min
Target Availability: 99.5%

┌──────────────────────────────────────────────────────────────┐
│                    OPTIMIZATION LAYERS                        │
└──────────────────────────────────────────────────────────────┘

1. CACHING LAYER (v2)
   ┌──────────────────────────────────────┐
   │ • Cache query embeddings (Redis)     │
   │ • Cache Qdrant results (5 min TTL)   │
   │ • Cache LLM responses (session TTL)  │
   └──────────────────────────────────────┘

2. CONNECTION POOLING
   ┌──────────────────────────────────────┐
   │ • PostgreSQL: max 10 connections     │
   │ • Qdrant: persistent HTTP client     │
   │ • OpenRouter: connection reuse       │
   └──────────────────────────────────────┘

3. ASYNC I/O
   ┌──────────────────────────────────────┐
   │ • FastAPI async endpoints            │
   │ • Concurrent sub-agent execution     │
   │ • Non-blocking database queries      │
   └──────────────────────────────────────┘

4. RESPONSE STREAMING (v2)
   ┌──────────────────────────────────────┐
   │ • Stream LLM tokens as generated     │
   │ • Reduce perceived latency           │
   │ • Better UX for long answers         │
   └──────────────────────────────────────┘

5. REQUEST QUEUING (v2)
   ┌──────────────────────────────────────┐
   │ • Rate limit: 100 req/min            │
   │ • Queue excess requests (Celery)     │
   │ • Graceful degradation under load    │
   └──────────────────────────────────────┘
```

---

**Last Updated**: 2026-01-03

**Status**: ⏸️ Architecture documented, awaiting implementation approval
