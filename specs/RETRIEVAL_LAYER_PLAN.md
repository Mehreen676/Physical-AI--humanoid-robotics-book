# Semantic Retrieval Layer - Implementation Plan

## Executive Summary

**Goal**: Build a reliable, deterministic semantic retrieval system that fetches relevant book content from Qdrant for RAG agent consumption.

**Status**: 📋 PLANNING PHASE

**Implementation Date**: 2026-01-03

**Location**: `retrieval/` directory (standalone module) or `backend/rag/` (if integrating with Step 2)

**Target Audience**: Hackathon judges, AI engineers validating retrieval before answer generation

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   SEMANTIC RETRIEVAL LAYER                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│              │         │              │         │              │
│ User Query   │────────▶│   Embedding  │────────▶│   Qdrant     │
│ (Plain Text) │         │   Service    │         │   Search     │
│              │         │              │         │              │
│ "What is     │         │ • Gemini or  │         │ • Cosine     │
│  ROS 2?"     │         │   Mock       │         │   similarity │
│              │         │ • 768-dim    │         │ • Top-k      │
│              │         │   vector     │         │ • Threshold  │
│              │         │              │         │              │
└──────────────┘         └──────────────┘         └──────────────┘
                                                           │
                                                           ▼
                                              ┌──────────────────┐
                                              │  Retrieved       │
                                              │  Chunks          │
                                              │                  │
                                              │ [                │
                                              │   {              │
                                              │     text: "...", │
                                              │     metadata: {  │
                                              │       chapter,   │
                                              │       section,   │
                                              │       source,    │
                                              │       chunk_idx  │
                                              │     },           │
                                              │     score: 0.85  │
                                              │   }              │
                                              │ ]                │
                                              └──────────────────┘
                                                           │
                                                           ▼
                                              ┌──────────────────┐
                                              │  Return to       │
                                              │  RAG Agent       │
                                              └──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    SELECTED TEXT MODE                            │
└─────────────────────────────────────────────────────────────────┘

User Selected Text: "ROS 2 provides real-time capabilities..."
      │
      ▼
┌──────────────┐
│ Embed        │  Generate embedding for selected text
│ Selection    │  (not the query!)
└──────────────┘
      │
      ▼
┌──────────────┐
│ Search       │  Find chunks similar to selection
│ Qdrant       │  (constrains retrieval context)
└──────────────┘
      │
      ▼
┌──────────────┐
│ Filter by    │  Only return chunks highly similar
│ High Score   │  to selected text (e.g., >0.85)
└──────────────┘
      │
      ▼
┌──────────────┐
│ Return       │  Relevant chunks from selected context
│ Subset       │  (agent answers only from this subset)
└──────────────┘
```

---

## Detailed Architecture

### Normal Retrieval Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     NORMAL RETRIEVAL                             │
└─────────────────────────────────────────────────────────────────┘

User Query: "What is ROS 2?"
      │
      ▼
┌──────────────────────────────────────────┐
│ Step 1: Validate Input                   │
│ • Check query is not empty               │
│ • Trim whitespace                        │
│ • Log query text (masked if PII)         │
└──────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────┐
│ Step 2: Generate Query Embedding         │
│ • Call embedding service (Gemini/Mock)   │
│ • Get 768-dimensional vector             │
│ • Log embedding generation success       │
│ • Cache embedding (optional)             │
└──────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────┐
│ Step 3: Search Qdrant                    │
│ • Collection: data_collection            │
│ • Query vector: [768-dim]                │
│ • Limit: k=5 (configurable)              │
│ • Score threshold: 0.7 (configurable)    │
│ • Distance metric: Cosine                │
└──────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────┐
│ Step 4: Format Results                   │
│ • Extract text and metadata              │
│ • Preserve chunk_index, total_chunks     │
│ • Include similarity score               │
│ • Sort by score (descending)             │
└──────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────┐
│ Step 5: Return Results                   │
│ [                                         │
│   {                                       │
│     "text": "ROS 2 is...",               │
│     "metadata": {                         │
│       "chapter": "Getting Started",      │
│       "section": "Introduction",         │
│       "source_file": "intro.md",         │
│       "chunk_index": 0,                  │
│       "total_chunks": 3                  │
│     },                                    │
│     "score": 0.89                        │
│   }                                       │
│ ]                                         │
└──────────────────────────────────────────┘
```

### Selected Text Retrieval Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  SELECTED TEXT RETRIEVAL                         │
└─────────────────────────────────────────────────────────────────┘

User Query: "How does this work?"
Selected Text: "ROS 2 provides real-time capabilities using DDS"
      │
      ▼
┌──────────────────────────────────────────┐
│ Step 1: Detect Selected Text Mode        │
│ • Check if selected_text is provided     │
│ • Validate selected_text is not empty    │
│ • Log mode: "selected_text"              │
└──────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────┐
│ Step 2: Embed Selected Text              │
│ • Generate embedding for selected_text   │
│ • NOT the query embedding!               │
│ • Get 768-dimensional vector             │
│ • Log embedding generation               │
└──────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────┐
│ Step 3: Search Qdrant                    │
│ • Collection: data_collection            │
│ • Query vector: selected_text embedding  │
│ • Limit: k=3 (fewer than normal)         │
│ • Score threshold: 0.85 (higher!)        │
│ • Distance metric: Cosine                │
└──────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────┐
│ Step 4: Filter Results                   │
│ • Only keep chunks with score >0.85      │
│ • Limit to top 3 most similar            │
│ • Remove duplicates if any               │
└──────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────┐
│ Step 5: Return Constrained Results       │
│ • Chunks semantically similar to         │
│   selected text                           │
│ • Agent will answer query using only     │
│   these chunks                            │
│ • If no results: return empty array      │
└──────────────────────────────────────────┘
```

---

## Section Structure

### Phase 1: Configuration & Setup ⏸️

**Duration**: 15 minutes

**Goal**: Set up retrieval module directory and configuration

**Tasks**:
- [ ] Create `retrieval/` directory (or `backend/rag/` if integrating with Step 2)
- [ ] Create configuration file `retrieval/config.py`
  - Qdrant connection parameters (URL, API key, collection name)
  - Retrieval parameters (top_k, score_threshold)
  - Embedding service configuration
- [ ] Create `.env` with retrieval-specific variables
  - `QDRANT_URL` (reuse from Step 1)
  - `QDRANT_API_KEY` (reuse from Step 1)
  - `COLLECTION_NAME` (reuse from Step 1)
  - `GEMINI_API_KEY` (reuse from Step 1)
  - `RETRIEVAL_TOP_K=5`
  - `RETRIEVAL_SCORE_THRESHOLD=0.7`
  - `SELECTED_TEXT_TOP_K=3`
  - `SELECTED_TEXT_SCORE_THRESHOLD=0.85`
- [ ] Create `requirements.txt`
  - qdrant-client
  - google-generativeai (or reuse embeddings from Step 1)
  - python-dotenv
  - pydantic (for validation)

**Output**: Configured retrieval module directory

**Dependencies**: Step 1 complete (Qdrant populated, embedding service available)

---

### Phase 2: Embedding Service Integration ⏸️

**Duration**: 20 minutes

**Goal**: Integrate embedding service for query vectorization

**Tasks**:
- [ ] Create `retrieval/embeddings.py`
  - Option A: Copy `ingestion/embeddings.py` (GeminiEmbeddings class)
  - Option B: Create symlink to `ingestion/embeddings.py`
  - Option C: Import from ingestion module
- [ ] Create `retrieval/mock_embeddings.py`
  - Copy `ingestion/mock_embeddings.py` (MockEmbeddings class)
  - Ensure same 768-dim output
- [ ] Create embedding service factory
  - `get_embedding_service()` function
  - Returns GeminiEmbeddings or MockEmbeddings based on config
  - Allows swapping without code changes
- [ ] Test embedding generation
  - Generate embedding for sample query
  - Verify 768 dimensions
  - Verify deterministic output (same query → same embedding)

**Output**: Working embedding service (Gemini or Mock)

**Dependencies**: Phase 1 (config loaded)

**Interface**:
```python
class EmbeddingService:
    def embed_query(self, text: str) -> List[float]:
        """Generate 768-dim embedding for query text."""
        pass

    def get_embedding_dimension(self) -> int:
        """Return 768."""
        pass
```

---

### Phase 3: Qdrant Retrieval Core ⏸️

**Duration**: 30 minutes

**Goal**: Implement core semantic search against Qdrant

**Tasks**:
- [ ] Create `retrieval/qdrant_client.py`
  - `QdrantRetriever` class
  - Initialize Qdrant client with URL, API key
  - Connection validation on init
- [ ] Implement `search()` method
  - Accept query vector, top_k, score_threshold
  - Call `qdrant_client.search()`
  - Return raw search results
- [ ] Implement result formatting
  - Extract text from payload
  - Extract metadata (chapter, section, source_file, chunk_index, total_chunks)
  - Include similarity score
  - Sort by score descending
- [ ] Add error handling
  - Connection failures → retry with exponential backoff
  - Empty results → return empty list (not error)
  - Invalid collection → raise clear error
- [ ] Add logging
  - Log search parameters (k, threshold)
  - Log number of results returned
  - Log retrieval latency

**Output**: Working Qdrant retrieval with formatted results

**Dependencies**: Phase 1 (config), Phase 2 (embeddings)

**Interface**:
```python
class QdrantRetriever:
    def __init__(self, url: str, api_key: str, collection_name: str):
        """Initialize Qdrant client."""
        pass

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Search Qdrant and return formatted results.

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
        pass
```

---

### Phase 4: Retrieval Orchestration ⏸️

**Duration**: 30 minutes

**Goal**: Orchestrate embedding + search with mode detection

**Tasks**:
- [ ] Create `retrieval/retriever.py`
  - `SemanticRetriever` class
  - Combines embedding service + Qdrant client
- [ ] Implement `retrieve()` method
  - Accept query, retrieval_mode, optional selected_text
  - Detect mode: "normal" or "selected_text"
  - Route to appropriate retrieval logic
- [ ] Implement normal retrieval
  - Embed query text
  - Search Qdrant with default params (k=5, threshold=0.7)
  - Return formatted results
- [ ] Implement selected text retrieval
  - Embed selected_text (NOT query!)
  - Search Qdrant with stricter params (k=3, threshold=0.85)
  - Filter results by high similarity
  - Return constrained results
- [ ] Add validation
  - Validate query is not empty
  - Validate selected_text in selected_text mode
  - Validate top_k and score_threshold ranges
- [ ] Add caching (optional)
  - Cache embeddings for repeated queries
  - TTL: 5 minutes

**Output**: Complete retrieval orchestrator with mode detection

**Dependencies**: Phase 2 (embeddings), Phase 3 (Qdrant)

**Interface**:
```python
class SemanticRetriever:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        qdrant_retriever: QdrantRetriever
    ):
        """Initialize with embedding service and Qdrant client."""
        pass

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
            List of retrieved chunks with metadata and scores
        """
        pass
```

---

### Phase 5: FastAPI Endpoint (Optional) ⏸️

**Duration**: 20 minutes

**Goal**: Create REST API endpoint for retrieval testing

**Tasks**:
- [ ] Create `retrieval/api.py`
  - FastAPI app with single endpoint
  - POST /retrieve
- [ ] Define request/response schemas
  - `RetrievalRequest`: query, mode, selected_text, top_k, threshold
  - `RetrievalResponse`: chunks, metadata (num_results, latency_ms)
- [ ] Implement endpoint handler
  - Initialize SemanticRetriever
  - Call retrieve()
  - Return formatted response
- [ ] Add CORS for frontend testing
- [ ] Add health check endpoint
  - GET /health
  - Check Qdrant connection
  - Check embedding service availability

**Output**: FastAPI endpoint for retrieval testing

**Dependencies**: Phase 4 (retriever)

**API Specification**:
```python
# POST /retrieve
{
  "query": "What is ROS 2?",
  "retrieval_mode": "normal",
  "selected_text": null,
  "top_k": 5,
  "score_threshold": 0.7
}

# Response
{
  "chunks": [
    {
      "text": "ROS 2 is...",
      "metadata": {
        "chapter": "Getting Started",
        "section": "Introduction",
        "source_file": "intro.md",
        "chunk_index": 0,
        "total_chunks": 3
      },
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

### Phase 6: Testing & Validation ⏸️

**Duration**: 30 minutes

**Goal**: Validate retrieval correctness and determinism

**Tasks**:

#### 6.1 Unit Tests
- [ ] Test embedding service (`tests/test_embeddings.py`)
  - Same query → same embedding (determinism)
  - Empty query → raises error
  - Mock vs Gemini produce 768-dim vectors
- [ ] Test Qdrant client (`tests/test_qdrant.py`)
  - Search returns expected format
  - Score threshold filters correctly
  - Top_k limits results
  - Connection error handling

#### 6.2 Integration Tests
- [ ] Test normal retrieval (`tests/test_retrieval.py`)
  - Query "What is ROS 2?" returns relevant chunks
  - Metadata is preserved
  - Scores are descending
  - Repeated queries return same results
- [ ] Test selected text retrieval
  - Constrains retrieval to selected context
  - Higher threshold filters aggressively
  - Returns fewer results than normal mode
- [ ] Test edge cases
  - Empty query → error
  - Query with no matches → empty list
  - Very long query → truncated or handled
  - Qdrant connection failure → clear error

#### 6.3 Manual QA
- [ ] Run sample queries
  - "What is ROS 2?" (should retrieve intro chunks)
  - "How do humanoid robots work?" (should retrieve robotics chunks)
  - "Explain vision-language-action" (should retrieve VLA chunks)
- [ ] Test selected text mode
  - Select passage about ROS 2
  - Ask "How does this work?"
  - Verify results are constrained to selection context
- [ ] Verify determinism
  - Run same query 3 times
  - Verify identical results (same chunks, same scores, same order)

**Output**: Comprehensive test suite with >90% coverage

**Dependencies**: All previous phases

---

### Phase 7: Documentation ⏸️

**Duration**: 25 minutes

**Goal**: Document retrieval API, usage, and examples

**Tasks**:
- [ ] Create `retrieval/README.md`
  - Quick start guide
  - Installation instructions
  - Configuration reference
  - Usage examples (normal + selected text)
- [ ] Create `specs/RETRIEVAL_EXAMPLES.md`
  - Sample queries with expected results
  - Normal retrieval examples
  - Selected text retrieval examples
  - Error handling examples
- [ ] Create `specs/RETRIEVAL_API.md`
  - Detailed API specification
  - Request/response schemas
  - Error codes
  - Performance characteristics
- [ ] Document retrieval modes
  - Normal mode: general semantic search
  - Selected text mode: constrained context search
  - When to use each mode
- [ ] Add inline docstrings
  - All public methods
  - Configuration parameters
  - Return types

**Output**: Complete documentation suite

**Dependencies**: All previous phases

---

## Completion Checklist

### Pre-Implementation ⏸️
- [ ] Step 1 complete (Qdrant collection populated)
- [ ] Embedding service available (Gemini or Mock)
- [ ] Qdrant credentials accessible
- [ ] Environment variables configured

### Core Implementation ⏸️
- [ ] Configuration setup
- [ ] Embedding service integration
- [ ] Qdrant retrieval core
- [ ] Retrieval orchestration with mode detection
- [ ] FastAPI endpoint (optional)

### Testing ⏸️
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration tests passing
- [ ] Edge cases tested
- [ ] Manual QA completed
- [ ] Determinism verified

### Documentation ⏸️
- [ ] README with usage guide
- [ ] API reference
- [ ] Examples documented
- [ ] Retrieval modes explained

---

## Time Estimates

| Phase | Estimated | Dependencies |
|-------|-----------|--------------|
| Configuration & Setup | 15 min | Step 1 complete |
| Embedding Service | 20 min | Phase 1 |
| Qdrant Retrieval Core | 30 min | Phase 1 |
| Retrieval Orchestration | 30 min | Phase 2, 3 |
| FastAPI Endpoint (Optional) | 20 min | Phase 4 |
| Testing & Validation | 30 min | All previous |
| Documentation | 25 min | All previous |
| **Total** | **170 min (2.8 hours)** | Sequential |

**Note**: Optional FastAPI endpoint adds 20 minutes. Without it, total is 150 minutes (2.5 hours).

---

## Critical Path

```
1. Phase 1: Configuration (15 min)
   ↓
2. Phase 2: Embedding Service (20 min)
   ↓
3. Phase 3: Qdrant Core (30 min)
   ↓
4. Phase 4: Orchestration (30 min)
   ↓
5. Phase 6: Testing (30 min)
   ↓
6. Phase 7: Documentation (25 min)
   ↓
7. ✅ Retrieval Layer Complete → Ready for RAG Agent Integration
```

**Optional**: Phase 5 (FastAPI endpoint) can be skipped if integrating directly with Step 2 RAG agent.

---

## Technology Stack

- **Vector Database**: Qdrant Cloud (Free Tier)
- **Embeddings**: Gemini embeddings-001 or MockEmbeddings (768-dim)
- **Similarity Metric**: Cosine similarity
- **Python Libraries**:
  - `qdrant-client` - Qdrant API client
  - `google-generativeai` - Gemini embeddings
  - `python-dotenv` - Configuration
  - `pydantic` - Validation
  - `fastapi` - REST API (optional)
  - `pytest` - Testing

---

## Configuration Reference

### Environment Variables

```bash
# Qdrant Configuration (from Step 1)
QDRANT_URL=https://87f0d492-3160-41ee-9a0d-9ff6295f2da5.europe-west3-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.LwaDQN_7WkP0DqLxGoHp2eWILkzFlcy6QPIY0um4o0k
COLLECTION_NAME=data_collection

# Embedding Service (from Step 1)
GEMINI_API_KEY=AIzaSyCTvAp39zQgXO7mFSQR92x5SGcN4ykqgh4
USE_MOCK_EMBEDDINGS=true  # Set to false after Gemini quota reset

# Retrieval Parameters - Normal Mode
RETRIEVAL_TOP_K=5
RETRIEVAL_SCORE_THRESHOLD=0.7

# Retrieval Parameters - Selected Text Mode
SELECTED_TEXT_TOP_K=3
SELECTED_TEXT_SCORE_THRESHOLD=0.85

# API Configuration (if using FastAPI endpoint)
RETRIEVAL_API_PORT=8001
```

### Configuration Class

```python
class RetrievalConfig:
    # Qdrant
    qdrant_url: str
    qdrant_api_key: str
    collection_name: str

    # Embeddings
    gemini_api_key: str
    use_mock_embeddings: bool = True

    # Normal Retrieval
    retrieval_top_k: int = 5
    retrieval_score_threshold: float = 0.7

    # Selected Text Retrieval
    selected_text_top_k: int = 3
    selected_text_score_threshold: float = 0.85

    # API (optional)
    api_port: int = 8001
```

---

## Success Metrics

- [ ] Sample query "What is ROS 2?" returns relevant chunks
- [ ] Retrieved chunks include complete metadata
- [ ] Repeated queries return identical results (determinism)
- [ ] Selected text mode constrains retrieval correctly
- [ ] No external knowledge introduced in retrieval
- [ ] Retrieval latency <500ms (P95)
- [ ] >90% test coverage
- [ ] Zero Qdrant connection failures in test set

---

## Risk Mitigation

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Gemini quota exhaustion | Medium | Use MockEmbeddings fallback | ✅ Handled (Step 1) |
| Qdrant connection failures | High | Retry logic + circuit breaker | ⏸️ Planned |
| Inconsistent retrieval results | High | Ensure deterministic embeddings | ⏸️ Planned |
| Low-quality selected text matches | Medium | Tune threshold (0.85 default) | ⏸️ Planned |
| Empty retrieval results | Low | Return empty list, log warning | ⏸️ Planned |

---

## Architectural Decisions

### 1. Why Separate Retrieval Layer?

**Decision**: Build retrieval as standalone module, not embedded in RAG agent

**Rationale**:
- **Testability**: Can validate retrieval independently before agent integration
- **Reusability**: Same retrieval logic usable by multiple consumers
- **Separation of concerns**: Retrieval ≠ reasoning
- **Debugging**: Easier to isolate retrieval issues

**Trade-off**: Slightly more code, but better architecture

### 2. Why Selected Text Uses Embedding of Selection?

**Decision**: Embed selected_text, not query, in selected text mode

**Rationale**:
- **Context constraint**: Want chunks similar to selection, not query
- **Better grounding**: Ensures answer is grounded in selected passage
- **User intent**: User highlighted passage they want to focus on

**Example**:
- Query: "How does this work?"
- Selected text: "ROS 2 uses DDS for real-time communication"
- Embedding selected text → retrieves chunks about DDS/communication
- Embedding query → would retrieve generic "how things work" chunks

### 3. Why Higher Threshold for Selected Text?

**Decision**: Use 0.85 threshold for selected text vs 0.7 for normal

**Rationale**:
- **Precision over recall**: Want highly relevant chunks only
- **Reduce noise**: Fewer but more accurate results
- **Better UX**: User expects answer grounded in their selection

**Trade-off**: May return no results if selection is too specific

### 4. Why Not Rerank with Cross-Encoder?

**Decision**: Use Qdrant's native cosine similarity only, no reranking

**Rationale**:
- **Simplicity**: Fewer dependencies, faster implementation
- **Latency**: Cross-encoder adds 200-500ms
- **Accuracy**: Gemini embeddings already high-quality
- **Scope**: Reranking is enhancement, not requirement

**Future**: Can add reranking in v2 if needed

---

## Integration with Step 2 (RAG Agent)

### How RAG Agent Will Use Retrieval Layer

```python
# In backend/agent/sub_agents.py

from retrieval.retriever import SemanticRetriever

class RetrievalSubAgent:
    def __init__(self):
        self.retriever = SemanticRetriever(
            embedding_service=get_embedding_service(),
            qdrant_retriever=get_qdrant_retriever()
        )

    async def retrieve(
        self,
        question: str,
        retrieval_mode: str,
        selected_text: Optional[str] = None
    ) -> List[Dict]:
        """Retrieve relevant chunks for question."""
        chunks = self.retriever.retrieve(
            query=question,
            retrieval_mode=retrieval_mode,
            selected_text=selected_text
        )
        return chunks
```

### Benefits for RAG Agent

1. **Pre-validated retrieval**: Retrieval logic already tested independently
2. **Clean interface**: Agent doesn't need to know about Qdrant/embeddings
3. **Mode detection handled**: Agent just passes retrieval_mode parameter
4. **Deterministic behavior**: Same question → same chunks → consistent answers

---

## Example Queries

### Normal Retrieval

**Query**: "What is ROS 2?"

**Expected Results**:
```json
[
  {
    "text": "ROS 2 (Robot Operating System 2) is the next generation of ROS, providing real-time capabilities and improved security for robotic applications.",
    "metadata": {
      "chapter": "Getting Started",
      "section": "Introduction to ROS 2",
      "source_file": "intro-ros2.md",
      "chunk_index": 0,
      "total_chunks": 3
    },
    "score": 0.89
  },
  {
    "text": "Unlike ROS 1, ROS 2 uses DDS (Data Distribution Service) for communication, enabling real-time performance and multi-robot coordination.",
    "metadata": {
      "chapter": "Getting Started",
      "section": "ROS 2 Architecture",
      "source_file": "ros2-architecture.md",
      "chunk_index": 1,
      "total_chunks": 4
    },
    "score": 0.85
  }
]
```

### Selected Text Retrieval

**Query**: "How does this enable real-time performance?"

**Selected Text**: "ROS 2 uses DDS (Data Distribution Service) for communication"

**Expected Results**:
```json
[
  {
    "text": "DDS provides quality-of-service (QoS) policies that guarantee real-time message delivery with bounded latency, essential for safety-critical robotics applications.",
    "metadata": {
      "chapter": "Getting Started",
      "section": "ROS 2 Architecture",
      "source_file": "ros2-architecture.md",
      "chunk_index": 2,
      "total_chunks": 4
    },
    "score": 0.91
  }
]
```

**Note**: Only 1 result because threshold is 0.85 and k=3 (fewer results in selected mode)

---

## Non-Functional Requirements

### 1. Deterministic Retrieval

**Requirement**: Identical inputs → identical outputs

**Implementation**:
- Use deterministic embeddings (same text → same vector)
- Qdrant search is deterministic for same query vector
- Sort results by score (break ties by chunk_index)
- No randomness in retrieval logic

**Validation**:
```python
# Test determinism
results1 = retriever.retrieve("What is ROS 2?")
results2 = retriever.retrieve("What is ROS 2?")
results3 = retriever.retrieve("What is ROS 2?")

assert results1 == results2 == results3
```

### 2. Clear Logging

**Requirement**: Log all retrieval steps for debugging

**Implementation**:
```python
logger.info(f"Retrieval request: query='{query}', mode={retrieval_mode}")
logger.info(f"Generated embedding: dimension={len(embedding)}")
logger.info(f"Qdrant search: k={top_k}, threshold={score_threshold}")
logger.info(f"Retrieved {len(results)} chunks in {latency_ms}ms")
```

### 3. No Vector Mutation

**Requirement**: Never modify stored vectors or metadata

**Implementation**:
- Use read-only Qdrant operations (search only)
- No upsert/delete/update calls
- Retrieval is pure function (no side effects)

### 4. Swappable Embeddings

**Requirement**: Change embedding provider without code changes

**Implementation**:
```python
def get_embedding_service() -> EmbeddingService:
    if os.getenv("USE_MOCK_EMBEDDINGS") == "true":
        return MockEmbeddings()
    else:
        return GeminiEmbeddings(api_key=os.getenv("GEMINI_API_KEY"))
```

---

## Deliverables Summary

1. **Retrieval Module** (`retrieval/`)
   - `config.py` - Configuration management
   - `embeddings.py` - Embedding service (Gemini/Mock)
   - `qdrant_client.py` - Qdrant search wrapper
   - `retriever.py` - Main orchestrator with mode detection
   - `api.py` - FastAPI endpoint (optional)

2. **Tests** (`tests/`)
   - `test_embeddings.py` - Embedding service tests
   - `test_qdrant.py` - Qdrant client tests
   - `test_retrieval.py` - Integration tests

3. **Documentation** (`specs/`)
   - `RETRIEVAL_LAYER_PLAN.md` - This document
   - `RETRIEVAL_EXAMPLES.md` - Usage examples
   - `RETRIEVAL_API.md` - API specification

4. **Configuration**
   - `.env` - Environment variables
   - `requirements.txt` - Python dependencies

---

**Last Updated**: 2026-01-03

**Status**: ⏸️ Planning complete, awaiting implementation approval

**Next Action**: Review plan → Get approval → Start Phase 1 (Configuration)
