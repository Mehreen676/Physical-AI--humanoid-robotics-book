# Agentic RAG Architecture Sketch

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AGENTIC RAG FLOW                              │
└─────────────────────────────────────────────────────────────────────┘

User Input
(question + optional selected text + session_id)
    │
    ▼
┌─────────────────────┐
│   FastAPI Endpoint  │  POST /api/v1/chat
│   (routes.py)       │  - Validates input
└─────────────────────┘  - Orchestrates flow
    │
    ▼
┌─────────────────────┐
│  Retrieval Layer    │  ✅ Already Built (Step 1 & 2)
│  (retrieval/)       │  - Semantic search via Qdrant
└─────────────────────┘  - Gemini embeddings
    │                    - Mode: normal vs selected-text
    │                    - Returns: top-k chunks + metadata
    ▼
  Retrieved Chunks
  [
    {text: "...", metadata: {chapter, section}, score: 0.85},
    {text: "...", metadata: {chapter, section}, score: 0.82},
    ...
  ]
    │
    ▼
┌─────────────────────┐
│  Context Formatter  │  NEW
│  (chatkit_agent.py) │  - Formats chunks as agent context
└─────────────────────┘  - Adds grounding instructions
    │                    - Prepares system message
    ▼
  Formatted Context
  """
  CONTEXT FROM BOOK:
  [1] Chapter 1, Section 1.2: ROS 2 is...
  [2] Chapter 2, Section 2.1: Key improvements...
  """
    │
    ▼
┌─────────────────────┐
│  OpenAI Agent       │  NEW (ChatKit SDK)
│  (ChatKit SDK)      │  - Processes question with context
└─────────────────────┘  - Enforces grounding rules
    │                    - Generates answer or refusal
    │                    - Temperature = 0 (deterministic)
    ▼
  Agent Response
  {
    answer: "ROS 2 is... [Chapter 1, Section 1.2]",
    grounded: true
  }
    │
    ├──────────────────────────────────┐
    │                                  │
    ▼                                  ▼
┌─────────────────────┐      ┌─────────────────────┐
│  Neon Postgres      │      │  Response Formatter │
│  (Chat History)     │      │  (routes.py)        │
└─────────────────────┘      └─────────────────────┘
    │                                  │
    │ Store Turn:                      │ Build Response:
    │ - session_id                     │ - answer
    │ - question                       │ - citations
    │ - context_chunk_ids              │ - grounded flag
    │ - answer                         │ - metadata
    │ - grounded                       │
    │ - timestamp                      │
    │                                  │
    └──────────────────────────────────┘
                    │
                    ▼
            Return to User
            {
              session_id: "...",
              answer: "...",
              citations: [...],
              grounded: true,
              metadata: {...}
            }
```

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           COMPONENTS                                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│  FastAPI Layer  │  Orchestration & API
├─────────────────┤
│ • routes.py     │  POST /chat, POST /sessions, GET /sessions/{id}
│ • middleware    │  CORS, error handling
└─────────────────┘
        │
        ├──────────────────────────────────┐
        │                                  │
        ▼                                  ▼
┌─────────────────┐              ┌─────────────────┐
│ Retrieval Layer │              │  Agent Layer    │
│ (retrieval/)    │              │ (agent/)        │
├─────────────────┤              ├─────────────────┤
│ ✅ COMPLETE     │              │ NEW             │
│                 │              │                 │
│ • retriever.py  │              │ • chatkit_agent │
│ • embeddings.py │              │ • context_fmt   │
│ • qdrant_client │              │ • grounding     │
└─────────────────┘              └─────────────────┘
        │                                  │
        ▼                                  ▼
┌─────────────────┐              ┌─────────────────┐
│  Qdrant Cloud   │              │ OpenAI Agent    │
│  (Vector DB)    │              │ (ChatKit SDK)   │
├─────────────────┤              ├─────────────────┤
│ • Semantic      │              │ • Reasoning     │
│   search        │              │ • Grounding     │
│ • Cosine sim    │              │ • Refusal       │
└─────────────────┘              └─────────────────┘

                  ┌─────────────────┐
                  │ Storage Layer   │
                  │ (storage/)      │
                  ├─────────────────┤
                  │ NEW             │
                  │                 │
                  │ • database.py   │
                  │ • neon_client   │
                  └─────────────────┘
                          │
                          ▼
                  ┌─────────────────┐
                  │ Neon Postgres   │
                  │ (Serverless)    │
                  ├─────────────────┤
                  │ • sessions      │
                  │ • chat_turns    │
                  └─────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DATA FLOW                                   │
└─────────────────────────────────────────────────────────────────────┘

NORMAL MODE:
User Question: "What is ROS 2?"
    │
    ▼
[Retrieval Layer]
    │ Embed query with Gemini
    │ Search Qdrant (k=5, threshold=0.7)
    ▼
Chunks: [
  {text: "ROS 2 is...", chapter: "Ch1", section: "1.2", score: 0.85},
  {text: "Improvements...", chapter: "Ch2", section: "2.1", score: 0.82},
  ...
]
    │
    ▼
[Context Formatter]
    │ Format as numbered list
    │ Add metadata headers
    ▼
Context:
"""
You must answer using ONLY this context:

[1] Chapter 1, Section 1.2 (score: 0.85)
ROS 2 is the next generation of the Robot Operating System...

[2] Chapter 2, Section 2.1 (score: 0.82)
Key improvements in ROS 2 include real-time capabilities...
"""
    │
    ▼
[OpenAI Agent]
    │ System: "Use only provided context, cite sources"
    │ User: "What is ROS 2?"
    │ Context: [formatted above]
    ▼
Agent Response:
"ROS 2 is the next generation of the Robot Operating System with
improvements including real-time capabilities. [Chapter 1, Section 1.2;
Chapter 2, Section 2.1]"
    │
    ▼
[Storage]
    │ session_id: abc-123
    │ question: "What is ROS 2?"
    │ context_chunk_ids: [chunk_1, chunk_2]
    │ answer: "ROS 2 is..."
    │ grounded: true
    ▼
Neon Postgres: chat_turns table
    │
    ▼
[Response]
Return to user with citations


SELECTED-TEXT MODE:
User Question: "Explain this"
Selected Text: "DDS is used for communication"
    │
    ▼
[Retrieval Layer]
    │ Embed SELECTED TEXT (not question!)
    │ Search Qdrant (k=3, threshold=0.85)
    ▼
Chunks: [
  {text: "DDS (Data Distribution Service)...", chapter: "Ch3", score: 0.88}
]
    │
    ▼
[Context Formatter]
Context:
"""
SELECTED TEXT: "DDS is used for communication"

You must answer using ONLY context related to this selection:

[1] Chapter 3, Section 3.4 (score: 0.88)
DDS (Data Distribution Service) is the middleware used for
inter-node communication in ROS 2...
"""
    │
    ▼
[OpenAI Agent]
    │ Additional instruction: "Focus on selected text"
    │ Context: constrained to selection
    ▼
Agent Response:
"DDS (Data Distribution Service) is the middleware used for inter-node
communication in ROS 2. [Chapter 3, Section 3.4]"
    │
    ▼
[Storage + Response]
```

---

## Sequence Diagram

```
User    FastAPI   Retrieval   Context    Agent    Storage   Response
 │         │          │          │          │         │         │
 │ POST    │          │          │          │         │         │
 ├────────>│          │          │          │         │         │
 │ /chat   │          │          │          │         │         │
 │         │          │          │          │         │         │
 │         │ retrieve │          │          │         │         │
 │         ├─────────>│          │          │         │         │
 │         │          │          │          │         │         │
 │         │<─────────┤          │          │         │         │
 │         │ chunks   │          │          │         │         │
 │         │          │          │          │         │         │
 │         │   format context    │          │         │         │
 │         ├────────────────────>│          │         │         │
 │         │          │          │          │         │         │
 │         │<────────────────────┤          │         │         │
 │         │   formatted         │          │         │         │
 │         │          │          │          │         │         │
 │         │   invoke agent      │          │         │         │
 │         ├───────────────────────────────>│         │         │
 │         │          │          │          │         │         │
 │         │<───────────────────────────────┤         │         │
 │         │   answer            │          │         │         │
 │         │          │          │          │         │         │
 │         │   store turn        │          │         │         │
 │         ├─────────────────────────────────────────>│         │
 │         │          │          │          │         │         │
 │         │<─────────────────────────────────────────┤         │
 │         │   saved             │          │         │         │
 │         │          │          │          │         │         │
 │         │   build response    │          │         │         │
 │         ├────────────────────────────────────────────────────>│
 │         │          │          │          │         │         │
 │<────────┤          │          │          │         │         │
 │ response│          │          │          │         │         │
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       ERROR HANDLING                                 │
└─────────────────────────────────────────────────────────────────────┘

Request → Validation
    │
    ├─ Invalid input? → 400 Bad Request
    │                   {error: "Question required"}
    │
    ▼
Retrieval Layer
    │
    ├─ Qdrant error? → Retry 3x → Still fails?
    │                              │
    │                              ▼
    │                          500 Internal Error
    │                          {error: "Retrieval failed"}
    │
    ├─ Empty results? → Log warning
    │                   │
    │                   ▼
    │               Continue with empty context
    │               (Agent will refuse)
    │
    ▼
Context Formatting
    │
    ├─ Formatting error? → 500 Internal Error
    │                      {error: "Context preparation failed"}
    │
    ▼
Agent Invocation
    │
    ├─ API key invalid? → 500 Internal Error
    │                     {error: "Agent authentication failed"}
    │
    ├─ Timeout? → Retry 1x → Still timeout?
    │                        │
    │                        ▼
    │                    500 Internal Error
    │                    {error: "Agent timeout"}
    │
    ├─ Rate limit? → 429 Too Many Requests
    │                {error: "Rate limit exceeded"}
    │
    ▼
Storage
    │
    ├─ Database error? → Log error
    │                   │
    │                   ▼
    │               Continue (return response)
    │               (History not saved, but answer returned)
    │
    ▼
Success Response
200 OK
{
  answer: "...",
  citations: [...],
  grounded: true
}
```

---

## Performance Characteristics

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LATENCY BREAKDOWN                            │
└─────────────────────────────────────────────────────────────────────┘

Total Request Latency (P95): ~3 seconds

┌──────────────────────────────────────────────────────┐
│ Phase                │ P50    │ P95    │ P99         │
├──────────────────────┼────────┼────────┼─────────────┤
│ Input Validation     │  5ms   │  10ms  │  20ms       │
│ Retrieval (Qdrant)   │ 300ms  │ 500ms  │ 700ms       │
│ Context Formatting   │  20ms  │  40ms  │  60ms       │
│ Agent Processing     │ 1.5s   │ 2.5s   │ 3.5s        │
│ Storage (Neon)       │ 100ms  │ 200ms  │ 300ms       │
│ Response Formatting  │  10ms  │  20ms  │  30ms       │
├──────────────────────┼────────┼────────┼─────────────┤
│ TOTAL                │ 1.9s   │ 3.3s   │ 4.6s        │
└──────────────────────────────────────────────────────┘

Bottleneck: Agent Processing (OpenAI API call)
- Temperature=0 for determinism (may be slightly slower)
- Context size affects latency (more chunks = longer processing)

Optimization Opportunities:
1. Cache identical questions (deterministic responses)
2. Parallel retrieval + history loading
3. Connection pooling for Neon Postgres
4. Timeout agent calls at 5 seconds
```

---

## Deployment Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DEPLOYMENT ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │   User Client   │
                    │  (Frontend UI)  │
                    └─────────────────┘
                            │
                            │ HTTPS
                            ▼
                    ┌─────────────────┐
                    │   Railway /     │
                    │   Render        │
                    │  (FastAPI App)  │
                    └─────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Qdrant    │    │  OpenAI     │    │    Neon     │
│   Cloud     │    │  Agents SDK │    │  Postgres   │
│  (Vector)   │    │   (Agent)   │    │  (History)  │
└─────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │
        │                   │                   │
    Free Tier          Pay-per-use         Free Tier
    (Already           (API calls)        (Serverless)
     setup)

Environment Variables (Backend):
- OPENAI_API_KEY
- DATABASE_URL (Neon)
- QDRANT_URL
- QDRANT_API_KEY
- GEMINI_API_KEY

All secrets stored in Railway/Render environment config.
No secrets exposed to frontend.
```

---

## Context Window Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CONTEXT WINDOW MANAGEMENT                         │
└─────────────────────────────────────────────────────────────────────┘

Agent Model: GPT-4 Turbo / GPT-4o
Context Window: 128k tokens

Context Budget Allocation:
┌─────────────────────────────────────────┐
│ System Instructions      │ ~500 tokens  │ Fixed
│ Retrieved Book Chunks    │ ~4000 tokens │ Variable (top-5 chunks)
│ Conversation History     │ ~1500 tokens │ Variable (last 3 turns)
│ User Question            │ ~100 tokens  │ Variable
│ Agent Response           │ ~500 tokens  │ Output
├─────────────────────────────────────────┤
│ TOTAL                    │ ~6600 tokens │ Well within limit
└─────────────────────────────────────────┘

Chunk Size Calculation:
- Average chunk: 400 tokens (from ingestion CHUNK_SIZE=400)
- Top-k chunks: 5 (normal mode) or 3 (selected-text mode)
- Normal mode: 5 × 400 = 2000 tokens
- Selected-text: 3 × 400 = 1200 tokens

Overflow Strategy (if needed):
1. Truncate conversation history (keep last 2 turns instead of 3)
2. Reduce top-k (use top-3 instead of top-5)
3. Truncate individual chunks at 300 tokens
4. As last resort: return error "Context too large"

Current Implementation: No truncation needed (well within limits)
```

---

## Grounding Validation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GROUNDING VALIDATION                              │
└─────────────────────────────────────────────────────────────────────┘

Agent generates answer
    │
    ▼
Extract claims from answer
    │ Example: "ROS 2 is X. It has feature Y. [Chapter 1]"
    │ Claims:
    │   1. "ROS 2 is X"
    │   2. "It has feature Y"
    │   3. Citation: "[Chapter 1]"
    ▼
For each claim:
    │
    ├─ Check if claim appears in retrieved chunks
    │     │
    │     ├─ Exact match? ✅ Grounded
    │     ├─ Paraphrase match? ✅ Grounded (semantic similarity)
    │     └─ No match? ❌ Ungrounded
    │
    ▼
All claims grounded?
    │
    ├─ YES → grounded = true
    │         Return answer with citations
    │
    └─ NO → grounded = false
              Return refusal:
              "I cannot provide a fully grounded answer based on
               the book content provided."

Citation Validation:
    │
    ├─ Does citation reference actual chunk metadata?
    │     │
    │     ├─ Chapter/section matches? ✅ Valid
    │     └─ Doesn't match? ❌ Invalid (hallucinated citation)
    │
    ▼
Valid citations?
    │
    ├─ YES → Include citations in response
    └─ NO → Remove invalid citations, flag as partially grounded

Automated Validation (Post-processing):
    │
    ├─ Run keyword matching: answer keywords ⊆ chunk keywords
    ├─ Check chapter/section references exist in chunks
    ├─ Verify no external facts (e.g., dates, names not in chunks)
    │
    ▼
Validation Score: 0.0 - 1.0
    │
    ├─ Score ≥ 0.9 → Fully grounded ✅
    ├─ Score 0.7-0.9 → Mostly grounded ⚠️
    └─ Score < 0.7 → Not grounded ❌ (return refusal)
```

---

## Key Architectural Decisions

### 1. Separation of Concerns
```
Retrieval Layer (Step 1 & 2)
    ↓ Provides: chunks, metadata, scores
Agent Layer (Step 3 - NEW)
    ↓ Provides: reasoning, answer, citations
Storage Layer (Step 3 - NEW)
    ↓ Provides: persistence, history retrieval
```

**Rationale**: Clean interfaces, testable in isolation, reusable components

### 2. Agent-First vs Retrieval-First
```
✅ CHOSEN: Retrieval-First
   User Question → Retrieval → Agent (with context)

❌ REJECTED: Agent-First
   User Question → Agent (decides what to retrieve)
```

**Rationale**: Simpler, deterministic, agent focuses on reasoning not retrieval

### 3. Context Injection Strategy
```
✅ CHOSEN: Formatted System Message
   System: "Use only this context: [chunks]"
   User: "Question"

❌ REJECTED: Tool-based Retrieval
   Agent has tool to call retrieval on-demand
```

**Rationale**: Simpler, single agent call, no complex tool orchestration

### 4. Refusal Handling
```
✅ CHOSEN: Explicit Refusal Message
   "I cannot answer this question based on the book content provided."

❌ REJECTED: Best-effort Answer
   Try to answer anyway with disclaimer
```

**Rationale**: Clarity, avoids speculation, builds trust

### 5. Chat History Storage
```
✅ CHOSEN: Neon Serverless Postgres
   - Managed
   - Generous free tier
   - SQL queries for analytics

❌ REJECTED: In-memory (current)
   - Not persistent
   - Lost on restart

❌ REJECTED: Redis
   - Additional service
   - Cost overhead
```

**Rationale**: Persistence, scalability, cost-effective

---

## Migration from Step 2 to Step 3

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 2 → STEP 3 MIGRATION                         │
└─────────────────────────────────────────────────────────────────────┘

KEEP (No Changes):
✅ retrieval/ module (semantic search)
✅ FastAPI app structure
✅ API endpoint paths (/chat, /sessions, /health)
✅ Request/response schemas
✅ Environment variable management

REPLACE:
❌ backend/services/claude_service.py
   → NEW: backend/agent/chatkit_agent.py (OpenAI Agents SDK)

❌ backend/storage/sessions.py (in-memory)
   → NEW: backend/storage/database.py (Neon Postgres)

❌ backend/agent/sub_agents.py (custom orchestration)
   → NEW: Simplified orchestration using ChatKit

UPDATE:
🔄 backend/api/routes.py
   - Same endpoints
   - New internal flow (retrieval → ChatKit → Neon)

🔄 backend/config.py
   - Add DATABASE_URL
   - Add OPENAI_API_KEY
   - Remove OPENROUTER_API_KEY

🔄 backend/requirements.txt
   - Add: openai (OpenAI SDK)
   - Add: psycopg2-binary (Postgres)
   - Remove: (none - keep existing)

Migration Path:
1. Implement new components alongside existing
2. Test new flow in parallel
3. Switch endpoint to use new flow
4. Deprecate old components
5. Clean up unused code
```

This architecture is production-ready, scalable, and maintains strict grounding.
