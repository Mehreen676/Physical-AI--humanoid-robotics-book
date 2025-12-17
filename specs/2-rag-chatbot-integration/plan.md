# Implementation Plan: Integrated RAG Chatbot

**Feature**: RAG Chatbot Integration
**Feature Branch**: `2-rag-chatbot-integration`
**Created**: 2025-12-16
**Status**: Draft

---

## Technical Context *(mandatory)*

The Integrated RAG Chatbot transforms the static Docusaurus textbook into an interactive learning platform. It retrieves contextual information from book chapters using semantic search (Qdrant), generates answers with OpenAI's models, and enforces strict constraints to prevent hallucination. The system supports two query modes:

1. **Full Book Mode**: Query entire textbook content.
2. **Selected Text Mode**: Query only user-highlighted passages.

The architecture prioritizes:
- **Scalability**: Serverless components (FastAPI on serverless host, Neon, Qdrant Cloud).
- **Cost Efficiency**: Free-tier cloud services with pay-as-you-go OpenAI API usage.
- **Accuracy**: Strict prompt engineering and source citation.
- **Low Latency**: <6s end-to-end query response.

---

## Constitution Check *(mandatory)*

The plan aligns with the project's core principles:

- **Ethical AI Development**: RAG constraints prevent harmful hallucinations; transparent source attribution.
- **Robustness & Safety Engineering**: Strict error handling, rate limiting, and fallback responses.
- **Continuous Learning & Adaptation**: RAG pipeline enables dynamic content updates without model retraining.
- **Technical Standards**: Serverless design, encryption, observability, and adherence to free-tier service SLAs.

---

## Gates *(mandatory)*

- **Gate 1: Specification Clarity**: Spec is unambiguous and signed off. **PASS**
- **Gate 2: Service Availability**: Qdrant Cloud free tier confirmed; Neon free tier confirmed; OpenAI API verified. **PASS**
- **Gate 3: Integration Ready**: Docusaurus project structure exists and is deployed. **PASS (Phase 1 complete)**

---

## Architecture Sketch *(mandatory)*

### System Diagram (Textual)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docusaurus Textbook (Frontend)               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Chat UI Component (Sidebar/Modal)                         │   │
│  │ - Message display & input                                 │   │
│  │ - Text selection capture                                  │   │
│  │ - Session management UI                                   │   │
│  └──────────┬───────────────────────────────────────────────┘   │
│             │                                                    │
│  ┌──────────▼──────────────────────────────────────────────┐    │
│  │ JavaScript SDK (chat-embed.js)                          │    │
│  │ - Event handlers for selected text                      │    │
│  │ - API calls to backend                                  │    │
│  │ - Session storage (localStorage)                        │    │
│  └──────────┬───────────────────────────────────────────────┘    │
└─────────────┼───────────────────────────────────────────────────┘
              │
              │ HTTPS REST API Calls
              │
┌─────────────▼───────────────────────────────────────────────────┐
│              FastAPI Backend (RAG Service)                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ API Layer                                              │    │
│  │ - POST /query (full book)                              │    │
│  │ - POST /query-selected-text                            │    │
│  │ - POST /ingest (admin)                                 │    │
│  │ - GET /health                                          │    │
│  │ - GET /sessions/{session_id}                           │    │
│  └────────────┬──────────────────────────────────────────┘    │
│               │                                                 │
│  ┌────────────▼──────────────────────────────────────────┐    │
│  │ RAG Pipeline Orchestrator                             │    │
│  │ ┌──────────┐  ┌──────────┐  ┌──────────┐             │    │
│  │ │ Retrieval│→ │ Re-rank  │→ │Generation│             │    │
│  │ │ Agent    │  │ Agent    │  │ Agent    │             │    │
│  │ └──────────┘  └──────────┘  └──────────┘             │    │
│  └────────────┬──────────────────────────────────────────┘    │
│               │                                                 │
│  ┌────────────┴──────────────┬──────────────┬─────────────┐  │
│  │                           │              │             │  │
└──┼───────────────────────────┼──────────────┼─────────────┼──┘
   │                           │              │             │
   ▼                           ▼              ▼             ▼
┌────────────┐        ┌──────────────┐  ┌──────────┐  ┌──────────┐
│   Qdrant   │        │ Neon Postgres│  │ OpenAI  │  │ Sessions │
│ (Vectors)  │        │(Metadata &   │  │  API    │  │(in Neon) │
│            │        │ Chat History)│  │         │  │          │
└────────────┘        └──────────────┘  └──────────┘  └──────────┘

    Vector       Document &        LLM           Conversation
   Embeddings   Session Data    Generation        Persistence
```

### Component Responsibilities

#### 1. **Docusaurus Chat UI**
- Renders chat interface (sidebar or modal).
- Captures user messages and selected text.
- Displays responses with source citations.
- Manages session list and history.

#### 2. **JavaScript SDK (chat-embed.js)**
- Event listener for text selection (`document.onselectionchange`).
- API client for backend endpoints.
- Session storage via localStorage.
- Error handling and retry logic.

#### 3. **FastAPI Backend**
- Request validation and routing.
- Rate limiting and authentication (optional).
- Logging and error handling.

#### 4. **Retrieval Agent**
- Embeds user query via OpenAI embedding API.
- Queries Qdrant for top-k similar chunks.
- Filters by metadata (chapter, module) if specified.
- Returns ranked results.

#### 5. **Re-rank Agent**
- Optional step to refine Qdrant results using cross-encoder models or semantic relevance.
- Filters low-confidence results (score < threshold).

#### 6. **Generation Agent**
- Constructs prompt with retrieved context and strict constraints.
- Calls OpenAI API with structured response format.
- Formats response with citations.
- Enforces fallback for out-of-scope queries.

#### 7. **Data Layer**
- **Qdrant**: Stores embeddings + metadata (namespace per book/version).
- **Neon Postgres**: Stores chat sessions, messages, document metadata.
- **OpenAI API**: External LLM for embeddings and generation.

---

## Key Decisions and Rationale *(mandatory)*

### Decision 1: Vector Database Choice (Qdrant Cloud vs. FAISS)

| Aspect | Qdrant Cloud | FAISS |
|--------|--------------|-------|
| **Free Tier** | 1GB storage, unlimited queries | None (self-hosted only) |
| **Scalability** | Cloud-managed, multi-user, namespaced collections | Single-machine, limited scale |
| **Filtering** | Metadata filtering built-in | Requires custom indexing |
| **Management** | SaaS, no ops overhead | Manual deployment and maintenance |

**Decision**: **Qdrant Cloud** (Free Tier)
**Rationale**: Qdrant's free tier provides sufficient storage for ~200k chunks (typical large textbook), supports namespacing for book versioning, and requires zero operational overhead. FAISS would require self-hosted infrastructure, increasing deployment complexity.

---

### Decision 2: Embedding Model (OpenAI vs. Open-Source)

| Aspect | OpenAI text-embedding-3-small | Sentence Transformers |
|--------|-------------------------------|----------------------|
| **Quality** | SOTA; 1536-dim; optimized for retrieval | Good; 384/768-dim; varying quality |
| **Cost** | $0.02 per 1M tokens (minimal for RAG) | Free (self-hosted) |
| **Latency** | API call; ~200ms | Local; ~50ms |
| **Maintenance** | Zero ops | Requires model hosting |

**Decision**: **OpenAI text-embedding-3-small**
**Rationale**: Superior quality (important for RAG accuracy) and minimal cost. For a textbook with ~100k chunks, embedding cost is ~$2/month. The quality gain justifies the cost for accurate retrieval.

---

### Decision 3: LLM for Generation (GPT-4o vs. GPT-3.5-turbo)

| Aspect | GPT-4o | GPT-3.5-turbo |
|--------|--------|---------------|
| **Accuracy** | SOTA; better reasoning; lower hallucination | Good; occasional hallucinations; limited reasoning |
| **Cost** | $5/1M input, $15/1M output tokens | $0.5/1M input, $1.5/1M output tokens |
| **Latency** | ~3-4s (p95) | ~1-2s (p95) |

**Decision**: **GPT-4o** (with fallback to GPT-3.5-turbo)
**Rationale**: Superior accuracy reduces hallucination risk. For typical usage (500-1000 queries/month), cost is ~$5-10/month. The quality improvement justifies the cost for educational content. Implement fallback to GPT-3.5-turbo during high load or cost constraints.

---

### Decision 4: Selected-Text Mode Implementation

**Option A**: Client-side validation (JavaScript truncates selected text; backend trusts).
**Option B**: Server-side enforcement (backend validates context match).

**Decision**: **Hybrid (Option A + B)**
**Rationale**: Client-side truncates for UX (2000-token limit); server-side validates that response context is within selected text. This prevents both accidental and malicious bypass attempts.

---

### Decision 5: Chat History Storage

**Option A**: Neon Postgres (encrypted, persistent, searchable).
**Option B**: Redis (fast, in-memory, auto-expiry).
**Option C**: LocalStorage (client-side, no server cost).

**Decision**: **Neon Postgres (primary) + LocalStorage (cache)**
**Rationale**: Neon provides durable, searchable history accessible across devices. LocalStorage caches recent sessions for offline access. Combined approach balances durability and performance.

---

## Interfaces and API Contracts *(mandatory)*

### API Endpoints

#### 1. POST /query

**Purpose**: Answer a question using full book content.

**Request**:
```json
{
  "query": "What are the differences between ROS 1 and ROS 2?",
  "session_id": "optional-session-uuid",
  "book_version": "v1.0",
  "filters": {
    "chapter": "optional-chapter-name",
    "module": "optional-module-name"
  }
}
```

**Response** (200 OK):
```json
{
  "response": "ROS 2 improves upon ROS 1 by...",
  "sources": [
    {
      "chapter": "Module 1: ROS 2 Fundamentals",
      "section": "ROS 2 vs ROS 1",
      "excerpt": "..."
    }
  ],
  "session_id": "session-uuid",
  "latency_ms": 4200,
  "confidence": 0.95
}
```

**Error** (400 Bad Request):
```json
{
  "error": "Invalid request",
  "message": "query cannot be empty"
}
```

**Error** (429 Too Many Requests):
```json
{
  "error": "Rate limit exceeded",
  "retry_after_seconds": 60
}
```

---

#### 2. POST /query-selected-text

**Purpose**: Answer a question using only user-selected text.

**Request**:
```json
{
  "query": "What design principles are mentioned?",
  "selected_text": "Design principles for humanoid robots...",
  "session_id": "optional-session-uuid",
  "book_version": "v1.0"
}
```

**Response** (200 OK):
```json
{
  "response": "The selected text mentions...",
  "in_selected_text": true,
  "sources": [
    {
      "type": "selected_text",
      "excerpt": "..."
    }
  ],
  "session_id": "session-uuid",
  "latency_ms": 3800
}
```

**Response** (200 OK, out-of-scope):
```json
{
  "response": "The selected text does not contain the answer.",
  "in_selected_text": false,
  "session_id": "session-uuid"
}
```

---

#### 3. POST /ingest

**Purpose**: Ingest or update book chapters (admin endpoint).

**Request**:
```json
{
  "book_version": "v1.0",
  "chapters": [
    {
      "chapter": "Module 1",
      "section": "ROS 2 Fundamentals",
      "doc_name": "module-1-ros2.md",
      "content": "Full chapter markdown content..."
    }
  ],
  "skip_duplicates": true
}
```

**Response** (200 OK):
```json
{
  "ingested": 15,
  "skipped_duplicates": 3,
  "failed": 0,
  "vectors_stored": 15,
  "namespaces": ["book_v1.0"]
}
```

---

#### 4. GET /health

**Purpose**: Service health check.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "components": {
    "qdrant": "ok",
    "neon": "ok",
    "openai": "ok"
  },
  "version": "1.0.0"
}
```

---

#### 5. GET /sessions/{session_id}

**Purpose**: Retrieve conversation history.

**Response** (200 OK):
```json
{
  "session_id": "session-uuid",
  "created_at": "2025-12-16T10:00:00Z",
  "messages": [
    {
      "message_id": "msg-1",
      "user_message": "What is ROS 2?",
      "assistant_response": "ROS 2 is...",
      "created_at": "2025-12-16T10:00:10Z"
    }
  ],
  "message_count": 5
}
```

---

## Non-Functional Requirements & Budgets *(mandatory)*

### Performance

| Metric | Target | Note |
|--------|--------|------|
| Retrieval Latency (p95) | ≤ 500ms | Qdrant query + embedding |
| Generation Latency (p95) | ≤ 5s | OpenAI API call |
| Total Query Latency (p95) | ≤ 6s | End-to-end |
| Embedding Generation | ≤ 200ms | Per 100 tokens |
| API Response Size | ≤ 10KB | JSON payload |

### Reliability

| Metric | Target |
|--------|--------|
| Uptime SLA | 99.5% (monthly) |
| Error Rate | < 1% |
| Circuit Breaker Threshold | 5 consecutive failures |
| Retry Policy | Exponential backoff; max 3 retries |

### Cost Budget (Monthly)

| Service | Free Tier | Cost |
|---------|-----------|------|
| Qdrant Cloud | 1GB storage; unlimited queries | $0 |
| Neon Postgres | 3GB storage; 20GB bandwidth | $0 |
| OpenAI Embeddings | N/A | ~$2 (for 100k chunks refreshed monthly) |
| OpenAI GPT-4o | N/A | ~$10-50 (1000 queries; ~5s per query) |
| FastAPI Hosting | Serverless (Render/Railway free tier) | $0-5 |
| **Total** | | **~$15-60/month** |

### Security

- API keys stored in `.env`; never in code.
- TLS 1.3 for all API calls.
- Rate limiting: 10 queries/min per session; 1000 queries/day per IP.
- Input validation: Query max 500 chars; selected text max 10k chars.
- Output: No PII in responses; no raw system prompts exposed.

---

## Data Management *(mandatory)*

### Data Storage

**Qdrant (Vector Storage)**:
- Namespace: `book_{version}` (e.g., `book_v1.0`)
- Collection: `chapters`
- Point structure: `{ id, vector, payload: { doc_id, chapter, section, chunk_id, content_hash } }`
- Index type: HNSW (Hierarchical Navigable Small World)
- Backup: Qdrant Cloud auto-backup (daily).

**Neon Postgres (Metadata & Sessions)**:
```sql
-- Documents table
CREATE TABLE documents (
  doc_id UUID PRIMARY KEY,
  book_version VARCHAR(10),
  chapter VARCHAR(100),
  section VARCHAR(100),
  doc_name VARCHAR(200),
  content_hash VARCHAR(64),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Chat sessions table
CREATE TABLE sessions (
  session_id UUID PRIMARY KEY,
  user_id VARCHAR(100) NULLABLE,
  book_version VARCHAR(10),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Chat messages table
CREATE TABLE messages (
  message_id UUID PRIMARY KEY,
  session_id UUID REFERENCES sessions(session_id),
  user_message TEXT,
  assistant_response TEXT,
  source_chunk_ids JSONB,
  mode VARCHAR(20), -- 'full_book' or 'selected_text'
  selected_text TEXT NULLABLE,
  latency_ms INTEGER,
  created_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_documents_book ON documents(book_version);
```

### Data Retention

- Chat messages: Retain for 1 year; archive older messages to cold storage.
- Document metadata: Retain indefinitely.
- Embeddings in Qdrant: Refresh monthly or on content update.

### Migration Strategy

When upgrading book versions:
1. Create new Qdrant collection/namespace.
2. Ingest updated chapters via `/ingest` endpoint.
3. Update default book_version in API config.
4. Migrate user sessions to new version (optional).

---

## Operational Readiness *(mandatory)*

### Observability

**Logging**:
- All API requests logged with request ID, latency, status.
- All Qdrant queries logged with query embedding, retrieved results, scores.
- All OpenAI API calls logged with tokens used, cost, latency.
- All errors logged with stack trace, context, recommendation.

**Metrics**:
- Query latency (histogram: p50, p95, p99).
- Error rate (per endpoint).
- Qdrant query latency.
- OpenAI token usage (cost tracking).
- Session creation rate.

**Traces**:
- Distributed tracing for end-to-end query flow (optional; use OpenTelemetry).

**Log Aggregation**:
- Stdout to FastAPI logging; forward to ELK stack or simple file rotation.

---

### Alerting

| Condition | Threshold | Action |
|-----------|-----------|--------|
| API Error Rate | > 1% | Page on-call engineer |
| Query Latency (p95) | > 8s | Escalate to performance team |
| Qdrant Down | Unavailable | Fallback to full-text search or degrade |
| OpenAI Rate Limit | Hit | Implement queue; notify ops |
| Neon Disk Usage | > 80% | Escalate; plan archive migration |

---

### Deployment & Rollback

**Deployment Pipeline**:
1. Commit code to feature branch.
2. CI/CD pipeline runs tests (unit, integration, RAG accuracy tests).
3. Deploy to staging environment; run smoke tests.
4. Tag release in git; create GitHub release.
5. Deploy to production via containerized deployment (Docker).
6. Monitor error rate for 10 minutes; auto-rollback if error rate > 5%.

**Rollback Strategy**:
- Keep previous 3 container images tagged in registry.
- Rollback via: `kubectl set image deployment/rag-api rag-api=rag-api:v1.2.0`.
- Rollback Qdrant/Neon migrations (rarely needed; immutable by default).

---

## Risk Analysis and Mitigation *(mandatory)*

### Risk 1: OpenAI API Cost Explosion

**Severity**: High | **Likelihood**: Medium | **Impact**: Budget overrun

**Mitigation**:
- Implement rate limiting (10 queries/min per session).
- Implement cost monitoring; alert if monthly cost exceeds $100.
- Use GPT-3.5-turbo fallback during high load or cost spike.
- Cache embeddings to avoid re-embedding same content.

---

### Risk 2: Qdrant Free Tier Storage Limit Exceeded

**Severity**: Medium | **Likelihood**: Low | **Impact**: New queries fail

**Mitigation**:
- Monitor Qdrant usage; alert at 80% full.
- Implement vector compression (quantization) to reduce size.
- Archive old book versions to cold storage.
- Document upgrade path to paid Qdrant tier.

---

### Risk 3: Hallucination in Selected-Text Mode

**Severity**: High | **Likelihood**: Low | **Impact**: Incorrect answers

**Mitigation**:
- Implement server-side validation: check that response context is within selected text.
- Use prompt template: "Answer ONLY based on provided text. If answer not found, respond: 'The selected text does not contain the answer.'"
- Implement confidence scoring; flag low-confidence responses.
- Test with 50+ diverse selected-text queries before production.

---

## Evaluation and Validation *(mandatory)*

### Definition of Done

- [ ] All functional requirements implemented and tested.
- [ ] RAG accuracy test: 20 queries, ≥90% correct answers with citations.
- [ ] Selected-text mode test: 20 queries, 100% restricted to selected text.
- [ ] Latency test: p95 latencies meet targets.
- [ ] Error handling test: All edge cases covered.
- [ ] Security test: API keys not exposed; rate limiting enforced.
- [ ] Integration test: Chatbot renders in Docusaurus; all endpoints accessible.
- [ ] Load test: 100 concurrent users; error rate < 1%.
- [ ] Accessibility test: Chat UI complies with WCAG 2.1 AA.

### Validation Checklist

```markdown
### Accuracy Validation
- [ ] Test 20 diverse queries; 18+ must have correct, sourced answers.
- [ ] Test 10 out-of-scope queries; all must respond with "I don't have information".
- [ ] Test 10 selected-text queries; all must restrict to selected text.

### Performance Validation
- [ ] Retrieval latency: 5 runs of 10 queries each; p95 ≤ 500ms.
- [ ] Generation latency: 5 runs of 10 queries each; p95 ≤ 5s.
- [ ] Total latency: 5 runs of 10 queries each; p95 ≤ 6s.

### Integration Validation
- [ ] Chat UI loads in Docusaurus without errors.
- [ ] Text selection detected and passed to backend.
- [ ] Responses displayed with citations.
- [ ] Session history persists across page reloads.

### Load Validation
- [ ] 50 concurrent users for 10 minutes; error rate < 1%.
- [ ] 100 concurrent users for 5 minutes; error rate < 2%; latency degradation < 20%.

### Security Validation
- [ ] No API keys in git history (check with `git log -S`).
- [ ] Rate limiting enforced: 10 queries/min per session.
- [ ] Input validation: Malformed JSON rejected; oversized queries rejected.
```

---

## Implementation Phases *(mandatory)*

### Phase 1: Core RAG Pipeline (Weeks 1-2)

**Deliverables**:
- FastAPI backend with `/query` and `/health` endpoints.
- Qdrant Cloud integration (vector storage).
- Neon Postgres integration (metadata storage).
- OpenAI API integration (embeddings + generation).
- Prompt templates with hallucination constraints.

**Dependencies**: None.

---

### Phase 2: Selected-Text Mode & UI (Weeks 2-3)

**Deliverables**:
- `/query-selected-text` endpoint.
- JavaScript SDK for text selection capture.
- Chat UI component (Docusaurus integration).
- Client-side validation and truncation.
- Server-side context validation.

**Dependencies**: Phase 1 complete.

---

### Phase 3: Session Management & History (Week 3)

**Deliverables**:
- `/sessions/{session_id}` endpoint.
- Chat history persistence in Neon.
- LocalStorage caching for offline access.
- Session list UI in Docusaurus.

**Dependencies**: Phase 1 & 2 complete.

---

### Phase 4: Testing, Optimization & Deployment (Week 4)

**Deliverables**:
- Comprehensive test suite (unit, integration, RAG accuracy).
- Load testing and performance tuning.
- Security hardening and penetration testing.
- Production deployment guide and runbooks.
- Documentation and user guide.

**Dependencies**: Phases 1-3 complete.

---

## Dependencies *(mandatory)*

1. **Docusaurus Project**: Must be deployed and accessible; Hackathon_I project readiness assumed.
2. **Qdrant Cloud Account**: Free tier signup required.
3. **Neon Postgres Account**: Free tier signup required.
4. **OpenAI API Key**: Account with credits required.
5. **FastAPI Hosting**: Serverless host (Render, Railway, Vercel) with deployment capability.

---

## Decisions Needing Documentation *(mandatory)*

1. **Rate Limiting Strategy**: Implement token bucket (10 queries/min) or sliding window? (See Decision Log)
2. **Fallback Behavior on API Failures**: Return cached response or error message? (Implement error message with retry guidance)
3. **Selected-Text Length Limit**: 2000 tokens or dynamic based on model? (Fixed 2000 tokens; clear user indication)
4. **Model Fallback Logic**: Use GPT-3.5-turbo on failure or queue? (Fallback to GPT-3.5-turbo; queue if available)

---

## Notes

- **Version Control**: All code in `2-rag-chatbot-integration` branch.
- **Code Standards**: Follow project constitution (see `.specify/memory/constitution.md`).
- **Containerization**: Docker image for FastAPI backend; deploy to serverless host.
- **Cost Tracking**: Monthly tracking of OpenAI API usage; report in retrospectives.
