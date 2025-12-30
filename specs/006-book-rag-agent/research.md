# Research Findings: BookRAGAgent Implementation

**Date**: 2025-12-30 | **Status**: ✅ Complete | **Phase**: Phase 0

## Research Summary

All technical decisions for BookRAGAgent implementation are validated and confirmed. No clarifications were needed because the specification and constitutional requirements fully determine the technology stack and architectural patterns.

---

## 1. Agent Orchestration Framework

### Decision: OpenAI Agents SDK + ChatKit SDK

**Rationale**:
- OpenAI Agents SDK provides native multi-agent orchestration with sub-agent messaging
- ChatKit SDK adds skill-based execution model (each skill is independently callable, composable)
- Direct alignment with user's feature description: "Main Agent: BookRAGAgent, Sub-Agents: RetrievalSubAgent, AnswerSubAgent, GuardrailsSubAgent, SelectionModeSubAgent, MemorySubAgent, Skills: VectorSearchSkill, SelectedTextOverrideSkill, GroundedSynthesisSkill, RetrievalValidationSkill, AntiHallucinationSkill, SessionPersistenceSkill"

**Alternatives Considered**:
- **LangGraph**: More heavyweight graph-based orchestration; better for complex workflows, overkill for this use case
- **AutoGen (by Microsoft)**: Research-focused, not optimized for production RAG; less deterministic
- **Custom Agent Framework**: Highest risk, no time benefit over proven SDKs

**Implementation Details**:
- BookRAGAgent is the main agent; receives user query
- Sub-agents are registered with BookRAGAgent; each handles a specific responsibility
- Skills are attached to sub-agents; each skill is a callable unit of work
- Execution flow is deterministic and debuggable (step-by-step logging)

**Source**: Feature specification, user input (AGENT ARCHITECTURE section)

---

## 2. LLM Provider & Model Selection

### Decision: OpenRouter (NOT OpenAI API directly)

**Rationale**:
- OpenRouter provides unified API for multiple LLM providers (OpenAI, Anthropic, Google, etc.)
- Cost-effective: no monthly minimums, pay-per-token
- Model flexibility: can swap Claude 3.5 Sonnet ↔ GPT-4o without code changes
- No vendor lock-in: if OpenAI pricing changes, switch providers in 1 line (env var)
- Constitution Requirement: "OpenRouter (LLM provider, NOT OpenAI API)" explicitly mandates this choice

**Model Selection**:
- **Recommended**: Claude 3.5 Sonnet (for reasoning about hallucination detection) OR GPT-4o (for speed)
- **Configurable**: Via `MODEL_NAME` environment variable (e.g., `claude-3-5-sonnet`, `gpt-4o`)
- **Tuning**: Can be changed post-deployment without rebuilding

**API Integration**:
- OpenRouter uses OpenAI-compatible API format (same endpoint signature)
- Request: POST to `https://openrouter.io/api/v1/chat/completions`
- Headers: `Authorization: Bearer OPENROUTER_API_KEY`, `HTTP-Referer: OPENROUTER_URL`
- Enables zero-code switching if standard OpenAI API is needed later

**Cost Considerations**:
- Claude 3.5 Sonnet: ~$3/$15 per 1M input/output tokens (as of 2025)
- GPT-4o: ~$2.50/$10 per 1M input/output tokens
- Fallback model (if needed): Claude 3 Haiku (much cheaper, suitable for guardrails-only passes)

**Source**: Constitution v2.0.0, feature specification, user input

---

## 3. Vector Database & Embeddings

### Decision: Qdrant Cloud + Cohere Embeddings

**Qdrant Cloud Choice**:
- **Why**: Managed vector database, free tier sufficient for single book (up to 10,000+ chunks)
- **Metadata Support**: Qdrant preserves payload metadata (URL, section, chunk_id) in search results—critical for citations
- **Python Client**: Official `qdrant-client` is production-ready, async-capable
- **Scaling**: Free tier → paid tier is seamless if book grows beyond free limits

**Cohere Embeddings Choice**:
- **Why**: Free tier with generous rate limits, 1024-dimensional embeddings, semantic quality
- **Alternative**: OpenAI embeddings (tied to OpenAI API spend), Hugging Face local (operational complexity)
- **Cohere Integration**: `cohere-python` SDK, simple API: `embed(texts=...)` → embeddings list

**Technical Flow**:
1. During ingestion (pre-deployment): Book chunks → Cohere embeddings → Qdrant collection
2. During runtime (query): User query → Cohere embedding → Qdrant semantic search → top-k chunks
3. VectorSearchSkill retrieves chunks with metadata; subsequent skills use the chunks

**Similarity Threshold**:
- Default: 0.7 (cosine similarity)—tunable via code/env var
- Rationale: ~70% semantic similarity usually indicates relevant chunks; below = "not found" fallback
- Validation: Will be tuned during implementation testing

**Source**: Feature specification, constitution requirements

---

## 4. Session Storage & Database

### Decision: Neon Serverless PostgreSQL

**Why Neon**:
- Serverless: auto-scaling, no ops overhead, pay-per-compute
- PostgreSQL: robust, ACID compliance, JSON support (for metadata)
- Neon's "autosuspend" feature: free tier scales down when idle
- Python Integration: `psycopg2` or async `asyncpg` are mature, well-tested

**Schema Design** (to be detailed in data-model.md):
- **Users**: user_id (UUID), created_at
- **Sessions**: session_id (UUID), user_id (FK), created_at, updated_at, metadata (JSON)
- **Messages**: message_id (UUID), session_id (FK), role (enum), content (text), metadata (JSON)

**Session Persistence Requirements**:
- Multi-turn conversations: store recent N messages (e.g., last 5)
- Context for follow-ups: MemorySubAgent reads prior messages, passes to LLM prompt
- Session retrieval: /sessions/{session_id} endpoint returns conversation history
- Data retention: 90 days default (per spec assumptions)

**Integration Pattern**:
- SessionPersistenceSkill: async calls to Neon via asyncpg (non-blocking)
- Latency impact: ~50-100ms per session read/write (acceptable, <5 sec budget)
- Failover: If Neon down, system returns "Unable to process request" (graceful degradation)

**Source**: Feature specification, constitution requirements

---

## 5. Web Framework & API Design

### Decision: FastAPI

**Why FastAPI**:
- **Async by default**: Python async/await for concurrent request handling
- **Type Safety**: Pydantic models for request/response validation and documentation
- **OpenAPI Auto-Docs**: Automatic `/docs` (Swagger UI) and `/redoc` endpoints
- **Minimal Boilerplate**: Route definition is simple, error handling is clean
- **Production-Ready**: Used by major tech companies, actively maintained

**API Endpoints** (preliminary):
1. **POST /chat**: Main RAG query endpoint
   - Request: `{ "question": string, "session_id": string, "selected_text"?: string }`
   - Response: `{ "answer": string, "citations": [...], "retrieved_chunks": [...] }`

2. **POST /sessions**: Create new session
   - Response: `{ "session_id": string, "created_at": timestamp }`

3. **GET /sessions/{session_id}**: Retrieve session history
   - Response: `{ "session_id": string, "messages": [...] }`

4. **GET /health**: Health check
   - Response: `{ "status": "healthy", "services": {...} }`

**Uvicorn Server**:
- ASGI server for FastAPI
- Production deployment: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
- Development: `uvicorn backend.main:app --reload`

**Middleware**:
- Request/response logging (without exposing secrets)
- Error handling (convert exceptions → JSON responses)
- CORS (if frontend on different domain)

**Source**: Industry best practices, specification requirements

---

## 6. Testing Strategy

### Decision: pytest + Mocks for External Services

**Unit Testing** (`tests/unit/`):
- **Scope**: Individual skills and components
- **Examples**:
  - `test_vector_search.py`: VectorSearchSkill with mocked Qdrant
  - `test_grounding.py`: Anti-hallucination logic with sample answers
  - `test_sessions.py`: Session persistence with mocked database
- **Tools**: pytest, `unittest.mock` for mocks
- **Benefits**: Fast feedback, deterministic, no external dependencies

**Integration Testing** (`tests/integration/`):
- **Scope**: Full agent orchestration flow
- **Examples**:
  - `test_agent_orchestration.py`: BookRAGAgent end-to-end with mocked services
  - `test_chat_endpoint.py`: /chat endpoint with mocked Qdrant and LLM
- **Mocks**: Fixture files for realistic responses (mock_qdrant.py, mock_openrouter.py)
- **Benefits**: Validate multi-step flows, ensure integration points work

**No Live External Service Tests**:
- **Why**: Live tests are flaky, slow, expensive (API charges)
- **Alternative**: Fixtures with realistic responses (sample_chunks.py, sample_responses.py)
- **Deployment Testing**: Manual testing in staging environment with real services

**Coverage Goals**:
- Unit: ≥80% code coverage for core skills
- Integration: ≥70% coverage for orchestration flows
- Manual testing: All user stories validated with real services before production

**Performance Testing**:
- Latency measurement: How long does full /chat flow take?
- Goal: <5 sec p95 (excluding network latency between services)
- Load test: Concurrent requests with multiple sessions

**Source**: Constitution (reproducibility requirement), industry best practices

---

## 7. Deployment & Environment Variables

### Environment Variables (Mandatory)

```bash
# Vector Database
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key
COLLECTION_NAME=book-chunks

# LLM Provider
OPENROUTER_API_KEY=your-api-key
OPENROUTER_URL=https://openrouter.io
MODEL_NAME=claude-3-5-sonnet  # or gpt-4o, etc.

# Database
DATABASE_URL=postgresql://user:password@host/dbname

# Server
BASE_URL=http://localhost:8000  # or production domain
```

### Startup Validation
- Application MUST validate all env vars at startup
- If any are missing: Print clear error and fail (e.g., "Missing required environment variable: OPENROUTER_API_KEY")
- Never log the actual secret values

### Deployment Contexts
- **Local Dev**: .env file in repo (in .gitignore)
- **Staging**: Env vars injected via container orchestration (Docker, Kubernetes)
- **Production**: Env vars from secure secret manager (AWS Secrets Manager, Azure Vault, etc.)

**Source**: Constitution Security-First Foundation principle

---

## 8. Error Handling & Graceful Degradation

### Service Failure Scenarios

1. **Qdrant Unavailable**
   - User sees: "The book is not yet indexed. Please try again later."
   - Logged: "Qdrant connection failed: {error}" (no secrets)

2. **OpenRouter Timeout**
   - User sees: "Unable to process request. Please try again."
   - Logged: "LLM request timeout after 30s"

3. **Neon Database Down**
   - User sees: "Unable to process request. Please try again."
   - System: Session storage skipped, but answer still returned (graceful degradation)
   - Logged: "Database unavailable; session persistence skipped"

4. **Hallucination Detected**
   - User sees: "The answer cannot be found in the provided book content. Please rephrase your question or try another topic."
   - Logged: "Hallucination veto; no grounding found for answer"

### Logging Strategy
- All errors logged with context (request_id, timestamp, error type)
- No secrets logged (API keys, auth tokens, sensitive user data)
- Structured logging (JSON format) for production analysis
- Levels: DEBUG (development), INFO (normal), WARNING (degraded), ERROR (failures)

---

## 9. Security Considerations

### Secrets Management
✅ All secrets from environment variables (no hardcoding)
✅ .env in .gitignore (never version-controlled)
✅ .env.example in repo with placeholder values
✅ Startup validation prevents silent failures from missing secrets
✅ No secrets logged or echoed in responses

### Input Validation
- Query max 500 characters (prevent token overflow)
- Chunks max 2000 characters (prevent context window issues)
- Special characters normalized (prevent injection attacks)
- Rate limiting (if needed): can be added as middleware

### Output Safety
- Answers synthesized only from retrieved chunks (prevent hallucination)
- Citations include source metadata (user can verify)
- Error messages generic (don't expose service details)
- Metadata cleaned (no internal IDs leaked)

**Source**: Constitution Security-First Foundation and Zero-Hallucination Grounding

---

## Summary & Sign-Off

### All Technical Decisions Validated ✅

| Decision | Status | Confidence |
|----------|--------|-----------|
| Agent Orchestration (OpenAI SDK) | ✅ Confirmed | 100% |
| LLM Provider (OpenRouter) | ✅ Confirmed | 100% |
| Vector Database (Qdrant Cloud) | ✅ Confirmed | 100% |
| Embeddings (Cohere) | ✅ Confirmed | 100% |
| Session Storage (Neon PostgreSQL) | ✅ Confirmed | 100% |
| Web Framework (FastAPI) | ✅ Confirmed | 100% |
| Testing Strategy (pytest + mocks) | ✅ Confirmed | 100% |
| Deployment & Secrets (env vars) | ✅ Confirmed | 100% |

### No Unresolved Clarifications
- Feature specification determined all technical choices
- Constitution requirements validated all choices
- No ambiguities remain; ready for design phase

### Proceed to Phase 1
- Generate `data-model.md`
- Create API contracts in `contracts/`
- Write `quickstart.md`
- Update agent context

---

**Next Command**: Phase 1 design artifacts (data-model.md, contracts, quickstart.md)
