# ADR-001: Vector Database Selection for RAG Chatbot

**Status**: Accepted
**Date**: 2025-12-16
**Feature**: RAG Chatbot Integration (#2)
**Deciders**: Technical Architecture Team
**Consulted**: Product Team, DevOps Team

---

## Context

The Integrated RAG Chatbot requires a vector database to store semantic embeddings of book chapters for efficient retrieval during query processing. The system needs to:

1. Store ~200k embeddings (1536-dimensional vectors) for a typical large textbook
2. Support semantic similarity search with sub-500ms latency
3. Enable metadata filtering by chapter, module, and book version
4. Operate on free or low-cost cloud services
5. Require minimal operational overhead
6. Support multi-tenancy for potential future book versions

The choice of vector database directly impacts:
- **Infrastructure costs**: $0-100+/month depending on service
- **Operational overhead**: Self-hosted vs. managed SaaS
- **Scalability**: From single book to multi-version systems
- **Data isolation**: Namespace support for versioning
- **Development velocity**: Time to first successful query

---

## Decision

**We will use Qdrant Cloud (Free Tier) as the vector database for the RAG Chatbot.**

### Selected Solution

**Qdrant Cloud**:
- Managed SaaS vector database with free tier offering 1GB storage
- HNSW (Hierarchical Navigable Small World) indexing for fast similarity search
- Built-in metadata filtering for chapter/module-based queries
- Namespace support for book version isolation
- REST API and Python SDK available
- No operational overhead; auto-scaling and backups handled by provider
- Free tier sufficient for textbook use case (~200k vectors × 8KB ≈ 1.6GB; optimized to fit 1GB)

---

## Rationale

### Trade-off Analysis

| Criterion | Qdrant Cloud | FAISS (Self-Hosted) | Pinecone | Weaviate |
|-----------|--------------|-------------------|----------|----------|
| **Cost** | $0 (free tier) | $0 (self-hosted) | $1+/month | $0 (self-hosted) |
| **Storage (Free)** | 1GB | Unlimited (self-hosted) | 1M vectors | 25GB |
| **Metadata Filtering** | ✅ Built-in | ⚠️ Custom implementation | ✅ Built-in | ✅ Built-in |
| **Namespaces** | ✅ Yes | ❌ No | ✅ Yes | ⚠️ Limited |
| **Ops Overhead** | ✅ Zero | ❌ High | ✅ Zero | ⚠️ Moderate |
| **Scaling** | ✅ Auto (SaaS) | ❌ Manual | ✅ Auto | ⚠️ Manual |
| **Latency (p95)** | <200ms | <50ms (local) | <200ms | <200ms |
| **Learning Curve** | Easy | Moderate | Easy | Moderate |
| **Community/Support** | Strong | Excellent | Good | Growing |

### Why Qdrant Cloud Won

1. **Free Tier Adequacy**: The 1GB free tier is sufficient for 200k vectors with metadata. Vector compression and deduplication strategies can optimize storage.

2. **Metadata Filtering**: Unlike FAISS, Qdrant supports first-class metadata filtering, enabling chapter-based filtering without custom indexing.

3. **Namespace Support**: Essential for future multi-version book support. Qdrant's collection/namespace structure naturally maps to book versions.

4. **Zero Operational Overhead**: Unlike self-hosted FAISS or Weaviate, Qdrant Cloud requires no DevOps effort:
   - No infrastructure provisioning
   - No database maintenance
   - Auto-scaling and backups handled
   - Enables faster time-to-first-query

5. **Cost Efficiency**: While Pinecone is comparable, Qdrant's free tier is more generous, and upgrade path to paid tier ($25+/month) is available when free tier is exceeded.

6. **Developer Experience**: REST API is clean; Python SDK (`qdrant-client`) integrates seamlessly with FastAPI.

### Alignment with Project Goals

- **Scalability**: Qdrant Cloud automatically scales; future paid tier supports unlimited vectors
- **Cost Efficiency**: Free tier aligns with project goal of using free cloud services
- **Robustness**: Managed service provides SLA and automatic failover
- **Continuous Learning**: Namespace structure supports dynamic content updates per version

---

## Consequences

### Positive

1. **Rapid Deployment**: No infrastructure setup required; can start queries immediately
2. **Minimal DevOps**: No database maintenance, backups, or scaling operations
3. **Future-Proof**: Easy upgrade to paid tier if 1GB is exceeded
4. **Metadata Flexibility**: Can add/modify chapter-level filtering without schema changes
5. **Developer Productivity**: Clean REST API reduces integration complexity

### Negative

1. **Storage Constraints**: 1GB free tier requires optimization; oversized books may not fit
   - **Mitigation**: Vector compression, archive old versions to cold storage
2. **Vendor Lock-In**: Moving to another vector DB requires data migration
   - **Mitigation**: Data can be exported; abstraction layer in code minimizes coupling
3. **Latency Variance**: Network latency (200-500ms) vs. local FAISS (<50ms)
   - **Mitigation**: Caching strategy; acceptable for interactive learning use case
4. **Upgrade Cost**: Scaling beyond 1GB requires paid plan (~$25+/month)
   - **Mitigation**: Acceptable cost; will evaluate after initial usage data

### Risks

- **Risk**: Free tier storage exceeded with large textbook
  - **Mitigation**: Implement vector compression; monitor usage; plan upgrade
- **Risk**: Qdrant service outage impacts RAG queries
  - **Mitigation**: Implement circuit breaker; degrade gracefully; fallback to semantic search via API

---

## Alternatives Considered

### Alternative 1: FAISS (Self-Hosted)

**Pros**:
- Zero cost
- Sub-50ms latency (local in-memory)
- Excellent for development

**Cons**:
- No built-in metadata filtering (requires custom implementation)
- Single-machine deployment; manual scaling
- Requires DevOps effort (deployment, updates, maintenance)
- No namespace support for multi-version books
- Cannot be easily deployed to serverless architecture

**Decision**: Rejected due to high operational overhead and lack of metadata support.

### Alternative 2: Pinecone

**Pros**:
- Fully managed SaaS (same as Qdrant)
- Excellent metadata filtering
- Strong enterprise support

**Cons**:
- Paid tier starts at $1/month (Qdrant is free)
- Larger free tier but more expensive at scale
- Higher cost trajectory ($25-100+/month depending on scale)
- Less community documentation than Qdrant

**Decision**: Rejected due to cost; Qdrant Cloud free tier is more generous.

### Alternative 3: Weaviate

**Pros**:
- Open-source option available
- Supports GraphQL queries
- Strong metadata support

**Cons**:
- Self-hosted requires DevOps effort
- Learning curve steeper than Qdrant
- Namespace support limited
- Community smaller than Qdrant

**Decision**: Rejected due to operational complexity.

---

## Implementation Notes

### Configuration

```python
# qdrant_integration.py
from qdrant_client import QdrantClient

# Connect to Qdrant Cloud
client = QdrantClient(
    url="https://your-cluster.qdrant.io",
    api_key="your-api-key"
)

# Create collection per book version
client.create_collection(
    collection_name="book_v1.0_chapters",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)
```

### Optimization Strategies

1. **Vector Compression**: Use scalar quantization to reduce 1536-dim → 1024-dim (-33% storage)
2. **Deduplication**: Hash-based deduplication of identical chunks
3. **Archiving**: Move old book versions to cold storage (S3) after initial ingestion
4. **Caching**: Implement query result caching to reduce repeated searches

---

## Future Review

**Review Date**: 2026-06-16 (6 months)

**Review Criteria**:
- Is 1GB storage sufficient? (Monitor usage monthly)
- Are latency targets being met? (Track p95 < 500ms)
- Is Qdrant meeting SLA? (Uptime > 99.5%)
- Do we need multi-version support? (Evaluate namespace usage)

**Potential Actions**:
- Upgrade to Qdrant paid tier if 1GB exceeded
- Migrate to Pinecone if cost becomes prohibitive at scale
- Evaluate new vector databases if Qdrant's roadmap diverges from needs

---

## References

- [Qdrant Cloud Documentation](https://qdrant.tech/documentation/)
- [Qdrant Free Tier Pricing](https://qdrant.io/pricing/)
- [Vector Database Comparison](https://airtable.com/appVJhFwK5dBrkJ29/shr9stkryPX1j88jC)
- Plan: `specs/2-rag-chatbot-integration/plan.md` (Decision 1: Vector Database Choice)
