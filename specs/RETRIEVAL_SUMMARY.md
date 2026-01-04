# Semantic Retrieval Layer - Summary

## Overview

**Goal**: Build a reliable, deterministic semantic search system that retrieves relevant book content from Qdrant for RAG agent consumption.

**Duration**: 2.5-2.8 hours (150-170 minutes)

**Status**: 📋 Planning complete, ready for implementation

**Target Audience**: Hackathon judges and AI engineers validating retrieval correctness

---

## What We're Building

A focused retrieval module that:
1. Accepts user queries as plain text
2. Generates query embeddings (Gemini or Mock)
3. Performs semantic search against Qdrant
4. Returns top-k relevant chunks with metadata
5. Supports "selected text only" retrieval mode
6. Provides deterministic, repeatable results

**Not building**: Answer generation, RAG agent, UI, reranking, analytics

---

## Architecture Summary

```
User Query
    ↓
Embedding Service (Gemini/Mock)
    ↓
Qdrant Semantic Search (Cosine)
    ↓
Formatted Results (chunks + metadata)
    ↓
Return to RAG Agent
```

### Two Retrieval Modes

**Normal Mode**:
- Embed user's question
- Search Qdrant (top_k=5, threshold=0.7)
- Return diverse, relevant chunks

**Selected Text Mode**:
- Embed user's selected text (not query!)
- Search Qdrant (top_k=3, threshold=0.85)
- Return chunks highly similar to selection
- Agent answers only from constrained context

---

## Key Features

### 1. Deterministic Retrieval
- Same query → same embeddings → same results
- No randomness in search or ranking
- Reproducible for testing and debugging

### 2. Metadata Preservation
Every result includes:
- Text content
- Chapter and section
- Source file
- Chunk index and total chunks
- Similarity score

### 3. Mode Detection
Automatically switches between normal and selected text retrieval based on input.

### 4. Swappable Embeddings
Use Gemini or Mock embeddings without code changes (configured via environment variable).

---

## Project Structure

```
retrieval/
├── __init__.py
├── config.py                # Configuration management
├── embeddings.py            # GeminiEmbeddings (from Step 1)
├── mock_embeddings.py       # MockEmbeddings (from Step 1)
├── qdrant_client.py         # Qdrant search wrapper
├── retriever.py             # Main orchestrator
└── api.py                   # FastAPI endpoint (optional)

tests/
├── test_embeddings.py       # Embedding service tests
├── test_qdrant.py           # Qdrant client tests
└── test_retrieval.py        # Integration tests

specs/
├── RETRIEVAL_LAYER_PLAN.md  # This comprehensive plan
├── RETRIEVAL_TASKS.md       # Task breakdown
├── RETRIEVAL_SUMMARY.md     # This summary
└── RETRIEVAL_EXAMPLES.md    # Usage examples (to be created)
```

---

## Implementation Phases

### Phase 1: Configuration (15 min)
- Create directory structure
- Configure environment variables
- Install dependencies

### Phase 2: Embedding Service (20 min)
- Integrate Gemini or Mock embeddings
- Create service factory for swapping
- Test embedding generation

### Phase 3: Qdrant Core (30 min)
- Implement Qdrant search wrapper
- Format results with metadata
- Add retry logic and error handling

### Phase 4: Orchestration (30 min)
- Build main retriever with mode detection
- Implement normal retrieval flow
- Implement selected text retrieval flow

### Phase 5: FastAPI Endpoint (20 min) - OPTIONAL
- Create REST API for testing
- Add health check endpoint

### Phase 6: Testing (30 min)
- Unit tests for each component
- Integration tests for full flow
- Verify determinism

### Phase 7: Documentation (25 min)
- README with usage guide
- API reference
- Examples

**Total**: 150 minutes without FastAPI, 170 minutes with FastAPI

---

## Configuration

### Environment Variables

```bash
# Qdrant (from Step 1)
QDRANT_URL=https://xxx.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your-key
COLLECTION_NAME=data_collection

# Embeddings (from Step 1)
GEMINI_API_KEY=your-key
USE_MOCK_EMBEDDINGS=true  # false after quota reset

# Retrieval Parameters - Normal Mode
RETRIEVAL_TOP_K=5
RETRIEVAL_SCORE_THRESHOLD=0.7

# Retrieval Parameters - Selected Text Mode
SELECTED_TEXT_TOP_K=3
SELECTED_TEXT_SCORE_THRESHOLD=0.85
```

### Why Different Parameters?

| Mode | top_k | Threshold | Rationale |
|------|-------|-----------|-----------|
| Normal | 5 | 0.7 | Diverse results, moderate precision |
| Selected Text | 3 | 0.85 | Fewer but highly relevant results |

---

## API Interface

### Main Retrieval Method

```python
class SemanticRetriever:
    def retrieve(
        self,
        query: str,
        retrieval_mode: Literal["normal", "selected_text"] = "normal",
        selected_text: Optional[str] = None,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Retrieve relevant chunks based on mode.

        Args:
            query: User's question
            retrieval_mode: "normal" or "selected_text"
            selected_text: Text selected by user (required if mode="selected_text")
            top_k: Override default top_k
            score_threshold: Override default threshold

        Returns:
            [
                {
                    "text": str,
                    "metadata": {
                        "chapter": str,
                        "section": str,
                        "source_file": str,
                        "chunk_index": int,
                        "total_chunks": int
                    },
                    "score": float
                }
            ]
        """
```

### FastAPI Endpoint (Optional)

```bash
# POST /retrieve
curl -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is ROS 2?",
    "retrieval_mode": "normal",
    "selected_text": null,
    "top_k": 5,
    "score_threshold": 0.7
  }'

# Response
{
  "chunks": [
    {
      "text": "ROS 2 is...",
      "metadata": {...},
      "score": 0.89
    }
  ],
  "metadata": {
    "num_results": 3,
    "latency_ms": 245,
    "retrieval_mode": "normal"
  }
}
```

---

## Example Queries

### Normal Retrieval

**Input**:
```python
results = retriever.retrieve(
    query="What is ROS 2?",
    retrieval_mode="normal"
)
```

**Output** (abbreviated):
```python
[
  {
    "text": "ROS 2 (Robot Operating System 2) is...",
    "metadata": {
      "chapter": "Getting Started",
      "section": "Introduction to ROS 2",
      "source_file": "intro-ros2.md",
      "chunk_index": 0,
      "total_chunks": 3
    },
    "score": 0.89
  },
  # ... up to 5 results
]
```

### Selected Text Retrieval

**Input**:
```python
results = retriever.retrieve(
    query="How does this work?",
    retrieval_mode="selected_text",
    selected_text="ROS 2 uses DDS for communication"
)
```

**Output** (abbreviated):
```python
[
  {
    "text": "DDS provides quality-of-service (QoS) policies...",
    "metadata": {
      "chapter": "Getting Started",
      "section": "ROS 2 Architecture",
      "source_file": "ros2-architecture.md",
      "chunk_index": 2,
      "total_chunks": 4
    },
    "score": 0.91
  }
  # ... up to 3 results, all score >0.85
]
```

---

## Success Metrics

- [ ] Query "What is ROS 2?" returns relevant chunks
- [ ] Retrieved chunks include complete metadata
- [ ] Repeated queries return identical results (determinism)
- [ ] Selected text mode constrains retrieval correctly
- [ ] No external knowledge introduced
- [ ] Retrieval latency <500ms (P95)
- [ ] >90% test coverage
- [ ] Zero connection failures in tests

---

## Dependencies

### On Step 1 (Ingestion)
- ✅ Qdrant collection `data_collection` populated (19 chunks)
- ✅ GeminiEmbeddings or MockEmbeddings code available
- ✅ Qdrant credentials accessible

### External Services
- Qdrant Cloud (Free Tier)
- Google Gemini API (Free Tier) or MockEmbeddings

### Python Version
- Python 3.11+ required

---

## Integration with Step 2 (RAG Agent)

### Before RAG Agent
Implement and test retrieval layer independently to validate:
1. Semantic search returns relevant results
2. Metadata is preserved correctly
3. Selected text mode works as expected
4. Retrieval is deterministic

### After Validation
Integrate into RAG agent's RetrievalSubAgent:
```python
from retrieval.retriever import SemanticRetriever

class RetrievalSubAgent:
    def __init__(self):
        self.retriever = SemanticRetriever(...)

    async def retrieve(self, question, mode, selected_text=None):
        return self.retriever.retrieve(question, mode, selected_text)
```

**Benefits**:
- Pre-tested retrieval logic
- Clean interface (agent doesn't know about Qdrant internals)
- Mode detection handled automatically
- Deterministic behavior guaranteed

---

## Key Design Decisions

### 1. Why Separate Retrieval Layer?
**Decision**: Build as standalone module, not embedded in RAG agent

**Rationale**:
- Testable independently before agent integration
- Reusable by multiple consumers
- Better separation of concerns (retrieval ≠ reasoning)
- Easier debugging and validation

### 2. Why Embed Selected Text Instead of Query?
**Decision**: In selected text mode, embed the selection, not the query

**Rationale**:
- Want chunks similar to selection, not query
- Better grounding in selected passage
- Matches user intent (focus on highlighted text)

**Example**:
- Query: "How does this work?"
- Selected text: "ROS 2 uses DDS for communication"
- Embedding selected text → retrieves DDS-related chunks ✅
- Embedding query → retrieves generic "how things work" chunks ❌

### 3. Why Higher Threshold for Selected Text?
**Decision**: Use 0.85 threshold vs 0.7 for normal

**Rationale**:
- Precision over recall (fewer but more accurate results)
- Reduce noise from irrelevant chunks
- User expects answer grounded in their specific selection

**Trade-off**: May return no results if selection is too specific

---

## Testing Strategy

### Unit Tests
- Embedding service returns 768-dim vectors
- Qdrant client formats results correctly
- Score threshold filters work
- Top-k limits results

### Integration Tests
- Normal retrieval returns relevant chunks
- Selected text mode constrains retrieval
- Metadata preserved in all results
- Same query → same results (determinism)

### Manual QA
- Test with sample queries from book
- Verify selected text mode behavior
- Confirm determinism with repeated queries

**Coverage Goal**: >90% line coverage

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Gemini quota exhaustion | Use MockEmbeddings fallback |
| Qdrant connection failures | Retry logic with exponential backoff |
| Inconsistent results | Ensure deterministic embeddings |
| Low-quality selected text matches | Tune threshold (0.85 default) |
| Empty results | Return empty list, log warning |

---

## Next Steps

### After Retrieval Layer Complete
1. **Validate independently**: Test retrieval before RAG agent integration
2. **Integrate with Step 2**: Use in RetrievalSubAgent
3. **Performance tuning**: Adjust thresholds if needed
4. **Monitoring**: Track retrieval latency and result quality

### Optional Enhancements (v2)
- Add caching for repeated queries (Redis)
- Implement reranking with cross-encoder
- Add metadata filtering (by chapter, section)
- Support hybrid search (semantic + keyword)

---

## Documentation Index

| Document | Purpose | Size |
|----------|---------|------|
| `RETRIEVAL_LAYER_PLAN.md` | Complete technical specification | 26 KB |
| `RETRIEVAL_TASKS.md` | Concise task breakdown | 8 KB |
| `RETRIEVAL_SUMMARY.md` | This executive summary | 6 KB |
| `RETRIEVAL_EXAMPLES.md` | Usage examples (to be created) | TBD |

---

## Quick Start

1. **Review Plan**: Read `RETRIEVAL_LAYER_PLAN.md`
2. **Setup**: Create `retrieval/` directory, install dependencies
3. **Implement**: Follow phases in `RETRIEVAL_TASKS.md`
4. **Test**: Verify determinism and correctness
5. **Validate**: Test with sample queries
6. **Integrate**: Use in Step 2 RAG agent

---

**Last Updated**: 2026-01-03

**Status**: 📋 Planning complete

**Estimated Time**: 2.5 hours (without FastAPI) or 2.8 hours (with FastAPI)

**Next Action**: Review documentation → Get approval → Start implementation
