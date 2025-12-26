# ADR 003: Database Architecture (Neon Postgres + Qdrant Separation)

**Status**: Accepted
**Date**: 2025-12-24
**Deciders**: Lead Architect, Backend Engineer
**Consulted**: None
**Informed**: All subagents

---

## Context

The project needs to store two types of data:
1. **Relational data**: Users, profiles, chat history, progress, preferences (ACID transactions needed)
2. **Vector data**: Embeddings for RAG retrieval (high-dimensional, semantic search needed)

Decision: Use one unified database (PostgreSQL with pgvector) or separate databases (Neon Postgres + Qdrant)?

### Options Considered

#### Option A: PostgreSQL Only (with pgvector Extension)
- **Pros**:
  - Single database to manage
  - ACID transactions guaranteed
  - Easier operational complexity
  - pgvector extension supports vectors
  - Cost-effective (one DB vs. two)
- **Cons**:
  - pgvector not as optimized for large-scale vector search (Qdrant is specialized)
  - Slower semantic search (not designed for it)
  - Mixing relational + vector queries complicates optimization
  - Scaling vector operations might lock relational data
  - pgvector maturity lower than Qdrant

#### Option B: Neon Postgres + Qdrant (Separate, Specialized)
- **Pros**:
  - **Separation of concerns**: Each DB optimized for its purpose
  - **Qdrant optimized**: Specialized vector DB (fast semantic search, optimized indexing)
  - **Scalability**: Vector operations don't impact relational data performance
  - **Technology fit**: Qdrant is industry-standard for RAG (used by OpenAI, Anthropic, etc.)
  - **Operational simplicity**: Managed services (Neon, Qdrant Cloud) reduce ops burden
  - **Future flexibility**: Can swap vector DB easily if needed
  - **Performance**: Qdrant's HNSW index much faster than pgvector
- **Cons**:
  - More operational complexity (manage two services)
  - Need to sync data (embeddings) across DBs
  - Data consistency challenges (eventual consistency, not ACID)
  - Two API clients to manage
  - Slightly higher cost (two services vs. one)
  - Potential latency (network calls to both services)

---

## Decision

**Use Neon Postgres + Qdrant (separate, specialized databases).**

### Rationale

1. **Specialized Tools**: Qdrant is purpose-built for vector search; PostgreSQL is for relational data. Each tool does its job best.

2. **Performance**: Qdrant's HNSW algorithm (Hierarchical Navigable Small World) is faster than pgvector for high-dimensional similarity search. RAG response time < 5s requires efficient retrieval.

3. **Scalability**: Vector indexing in Postgres locks relational queries. Separation avoids this contention.

4. **Industry Standard**: OpenAI, Anthropic, and other AI companies use dedicated vector DBs (Pinecone, Qdrant, Weaviate). RAG best practice.

5. **Operational Simplicity**: Both Neon and Qdrant are managed services (no ops overhead). Better than self-hosting both.

6. **Data Lifecycle**: Embeddings are derived data (can be regenerated). Relational data is transactional. Different consistency requirements justify separation.

---

## Consequences

### Positive
- ✅ Fast vector search (Qdrant optimized)
- ✅ Relational performance not impacted by vector ops
- ✅ Industry best practice
- ✅ Managed services (no self-hosting burden)
- ✅ Clear data ownership (Postgres = source of truth, Qdrant = derived cache)
- ✅ Flexibility (can swap Qdrant for Pinecone, Weaviate, etc.)
- ✅ Scalability (each service scales independently)

### Negative
- ⚠️ **Operational complexity**: Monitor two services, two APIs
- ⚠️ **Data sync**: Embeddings derived from chapters; must regenerate on chapter updates
- ⚠️ **Eventual consistency**: Qdrant might lag Postgres (embeddings not immediately searchable)
- ⚠️ **Cost**: Two services cost more than one (Qdrant Cloud ~$500-1000/mo at scale, Neon ~$100/mo)
- ⚠️ **Debugging**: Harder to debug queries across two systems
- ⚠️ **Network latency**: API calls to two services add ~10-50ms per query

### Mitigation Strategies
1. **Sync**: Embedding regeneration triggered on chapter content changes (automatic indexing pipeline)
2. **Cost**: Use Neon serverless (pay-per-query), Qdrant cloud free tier initially
3. **Latency**: Batch embedding generation, cache frequently-asked queries
4. **Operational**: Comprehensive monitoring (Sentry, custom dashboards) tracks both DBs
5. **Debugging**: Clear logging in embedding service (shows flow: Postgres → OpenAI → Qdrant)

---

## Data Flow Architecture

```
Chapter Content (Neon Postgres)
   ↓
[Content Ingestion & Chunking Service]
   ↓
[OpenAI Embeddings API]
   ↓
[Qdrant Vector Indexing]
   ↓
[Semantic Search (on user query)]
   ↓
[Retrieve context from Qdrant]
   ↓
[Format context, call GPT-4]
   ↓
Response
```

### Data Storage Map

**Neon Postgres** (Relational):
- Users, profiles, preferences
- Chat history, messages
- Chapters, metadata
- User progress, quiz scores
- **Source of truth** for business data

**Qdrant** (Vector):
- Chapter embeddings (chunks)
- Metadata (module, chapter, section)
- **Derived/cached data** (regenerable from chapters)
- **Used for**: Semantic search only

---

## Consistency Model

- **Strong consistency** (Postgres): User data, transactions
- **Eventual consistency** (Qdrant): Embeddings lag chapter updates by ~5-10 minutes (acceptable for educational content)
- **Solution**: Version embeddings (if chapter updates, regenerate embeddings for that chapter)

---

## Cost Analysis

**Estimated monthly costs**:
- Neon Postgres: $0-100 (free tier initially, serverless scaling)
- Qdrant Cloud: $0-500 (free tier ~1000 queries/mo, paid tier scales)
- OpenAI Embeddings: ~$10-20/mo (1536 dims, one-time indexing)
- OpenAI Chat (GPT-4): ~$50-100/mo (depends on chatbot usage)
- **Total**: ~$100-300/mo (small budget-friendly)

---

## Related Decisions

- **ADR 002**: RAG Architecture (requires Qdrant for fast vector search)
- **PLAN Phase 0.2**: Database setup
- **PLAN Phase 1.3**: Content indexing pipeline

---

## Approval

- ✅ **Lead Architect**: Approved (best-practices architecture, manageable cost, scalable)
- ✅ **Backend Engineer**: Approved (clear separation, proven technologies)

---

## References

- Qdrant vs. pgvector: https://qdrant.tech/articles/pgvector-alternative/
- HNSW Algorithm: https://arxiv.org/abs/1802.02413
- Neon: https://neon.tech/
- Managed Postgres comparison: https://cloud.google.com/sql/docs/postgres/introduction

