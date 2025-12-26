# ADR 002: RAG Chatbot Architecture (Qdrant + GPT-4 + Neon)

**Status**: Accepted
**Date**: 2025-12-24
**Deciders**: Lead Architect, Backend Engineer
**Consulted**: RoboticsExpert, Educator
**Informed**: All subagents

---

## Context

The project requires an embedded RAG (Retrieval-Augmented Generation) chatbot that answers questions about course content. Key decision: what architecture components to use?

### Options Considered

#### Option A: Simple FAQ-Based Q&A (No RAG)
- **Pros**:
  - Simplest implementation (hardcoded Q&A pairs)
  - Fast response times (no LLM calls)
  - Predictable, no hallucinations
- **Cons**:
  - Limited scope (only covers pre-written questions)
  - Doesn't leverage AI capabilities
  - Poor user experience (generic Q&A)
  - Doesn't align with "AI-native" project goal

#### Option B: Basic LLM Only (GPT-4, No Retrieval)
- **Pros**:
  - Flexible (can answer any question)
  - Advanced AI (GPT-4 capabilities)
  - Simple architecture (no retrieval component)
- **Cons**:
  - Hallucination risk (LLM makes up answers not in textbook)
  - Loss of grounding (can't cite sources)
  - Over-reliance on LLM knowledge (might be outdated)
  - Poor for specialized domain (robotics)
  - User distrust if answers are wrong

#### Option C: RAG with Vector Database (Qdrant + OpenAI Embeddings + GPT-4)
- **Pros**:
  - Best accuracy (responses grounded in course content)
  - User trust (can cite sources, "read the textbook")
  - Specialized knowledge (only answers questions about course)
  - Reduces hallucination (constrained to indexed content)
  - Scalable (new chapters automatically indexed)
  - State-of-the-art approach (modern LLM best practice)
  - Aligns with "RAG chatbot" project requirement
- **Cons**:
  - More complex architecture (retrieval + generation pipeline)
  - Requires vector DB setup (Qdrant)
  - Embeddings generation cost (OpenAI API)
  - RAG pipeline tuning needed (chunk size, retrieval ranking)
  - Higher latency (retrieval adds ~500ms-1s)

---

## Decision

**Implement full RAG pipeline: Qdrant vector DB + OpenAI embeddings + GPT-4 generation.**

### Rationale

1. **Project Requirement**: The spec explicitly calls for "RAG chatbot" with selected-text queries and context-aware answers. This architecture is the only one that meets the requirement.

2. **User Experience**: Students want reliable, grounded answers citing course materials, not generic LLM responses. RAG enables this.

3. **Domain Expertise**: Robotics/AI content is specialized. RAG ensures chatbot only answers questions the course covers, avoiding outdated or incorrect information.

4. **Accuracy & Trust**: Being able to cite sources ("This is mentioned in Chapter 1.3") builds user trust and improves learning outcomes.

5. **Scalability**: As chapters are added, they're automatically indexed. No manual Q&A maintenance.

6. **Modern Best Practice**: RAG is the current state-of-the-art for domain-specific Q&A. Aligns with "AI-native textbook" positioning.

---

## Consequences

### Positive
- ✅ Accurate, grounded responses (textbook-only answers)
- ✅ Source attribution (cite which chapter answered the question)
- ✅ Reduced hallucination risk
- ✅ Scalable (new chapters auto-indexed)
- ✅ Specialized knowledge (focused on course content)
- ✅ Modern AI architecture (impressive implementation)
- ✅ User trust and engagement (reliable answers)

### Negative
- ⚠️ **Complexity**: Retrieval + ranking + generation pipeline requires careful design
- ⚠️ **Latency**: RAG adds ~500ms-1s to response time (target < 5s acceptable but noticeable)
- ⚠️ **Cost**: Embedding generation (OpenAI API) and LLM calls (GPT-4) increase operational cost
- ⚠️ **Tuning required**: Chunk size, retrieval ranking, prompt engineering must be fine-tuned
- ⚠️ **Data quality**: Garbage in, garbage out—chapter content quality directly impacts chatbot quality
- ⚠️ **Knowledge cutoff**: Chatbot can't answer questions outside indexed content (by design, but users might expect more)

### Mitigation Strategies
1. **Latency**: Parallelize embeddings (batch processing), cache frequently-asked queries, optimize Qdrant indexes
2. **Cost**: Use cheaper embedding model (`text-embedding-3-small` not large), batch API calls, monitor usage
3. **Tuning**: Phase 1.3 dedicated to optimization, Phase 4.2 for enhancements (BM25 hybrid search, better ranking)
4. **Quality**: @RoboticsExpert reviews all chapter content before indexing
5. **User expectations**: Clear UI messaging ("I can only answer questions about the course")

---

## Component Architecture

```
User Query
   ↓
[Embedding] (OpenAI text-embedding-3-small)
   ↓
[Retrieval] (Qdrant semantic search, top-5)
   ↓
[Ranking] (re-rank by relevance, filter low-confidence)
   ↓
[Augmentation] (format context for LLM)
   ↓
[Generation] (GPT-4 with system prompt + context + query)
   ↓
[Filtering] (validate answer is grounded, reject out-of-scope)
   ↓
Response (answer + sources + confidence)
```

### Key Decisions Within RAG

1. **Embedding Model**: `text-embedding-3-small` (1536 dims, cheap, good quality)
   - Alternative: `text-embedding-3-large` (too expensive)

2. **Vector Database**: Qdrant (cloud or self-hosted)
   - Alternative: Pinecone (managed but pricey), Milvus (self-hosted, complex)
   - **Chose**: Qdrant for balance of ease + cost

3. **LLM**: GPT-4 (for quality responses)
   - Alternative: GPT-3.5 (cheaper, lower quality), Claude 3 (similar quality, different pricing)
   - **Chose**: GPT-4 for educational context (accuracy matters)

4. **Chunking**: 300-500 tokens with 100-token overlap
   - Alternative: 100-300 tokens (more chunks, slower), 500-1000 (fewer chunks, less context)
   - **Chose**: 300-500 for balance of specificity + context

5. **Retrieval Strategy**: Semantic search (cosine similarity) + BM25 hybrid (Phase 4.2)
   - Alternative: Keyword-only (poor quality), semantic-only (doesn't account for exact terms)
   - **Chose**: Start with semantic, add BM25 hybrid in advanced phase

---

## Implementation Timeline

- **Phase 0**: Qdrant setup, database schema (Task 0.2.3)
- **Phase 1.3.1-1.3.4**: Content indexing (embedding, chunking, Qdrant insertion)
- **Phase 1.3.5-1.3.8**: Retrieval, ranking, generation, API endpoint
- **Phase 4.2**: Enhancements (hybrid search, text selection query)

---

## Related Decisions

- **ADR 001**: Custom theme (requires custom chatbot widget component)
- **ADR 003**: Neon + Qdrant (separate DBs for relational + vector data)
- **PLAN Phase 1.3**: Detailed implementation plan

---

## Approval

- ✅ **Lead Architect**: Approved (aligns with project requirements, realistic timeline, manageable cost)
- ✅ **Backend Engineer**: Approved (clear architecture, proven components)
- ✅ **RoboticsExpert**: Approved (domain-specific Q&A benefits learning)

---

## References

- Qdrant: https://qdrant.tech/
- OpenAI Embeddings: https://platform.openai.com/docs/guides/embeddings
- RAG Best Practices: https://arxiv.org/abs/2005.11401

