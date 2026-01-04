# Semantic Retrieval Layer - Architecture Sketch

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL PIPELINE FLOW                           │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ User Input   │
│              │
│ • Query:     │  "What is ROS 2?"
│   "What is   │
│   ROS 2?"    │
│              │
│ • Optional:  │  (for selected-text mode)
│   Selected   │  "ROS 2 is a flexible architecture..."
│   Text       │
└──────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 1: INPUT HANDLING & VALIDATION                             │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ • Validate query is not empty                          │     │
│  │ • Detect retrieval mode:                               │     │
│  │   - Normal mode: query only                            │     │
│  │   - Selected-text mode: query + selected text          │     │
│  │ • Sanitize input (trim whitespace, length check)       │     │
│  │ • Log incoming request                                 │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 2: EMBEDDING GENERATION                                     │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Gemini Free-Tier Embeddings Service                    │     │
│  │                                                         │     │
│  │ Normal Mode:                                            │     │
│  │   Input: "What is ROS 2?"                              │     │
│  │   ↓                                                     │     │
│  │   embeddings-001 API                                    │     │
│  │   ↓                                                     │     │
│  │   Output: [0.023, -0.145, 0.089, ..., 0.234]          │     │
│  │           768-dimensional vector                        │     │
│  │                                                         │     │
│  │ Selected-Text Mode:                                     │     │
│  │   Input: "ROS 2 is a flexible architecture..."         │     │
│  │   ↓                                                     │     │
│  │   embeddings-001 API                                    │     │
│  │   ↓                                                     │     │
│  │   Output: [0.156, -0.023, 0.201, ..., 0.087]          │     │
│  │           768-dimensional vector                        │     │
│  │                                                         │     │
│  │ Rate Limiting: 15 requests/min (free-tier)             │     │
│  │ Error Handling: Fallback to MockEmbeddings if quota    │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 3: QDRANT SEMANTIC SEARCH                                   │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Qdrant Cloud Vector Search                             │     │
│  │                                                         │     │
│  │ Collection: data_collection                            │     │
│  │ Vector Dimension: 768                                   │     │
│  │ Distance Metric: Cosine Similarity                     │     │
│  │                                                         │     │
│  │ Normal Mode Parameters:                                 │     │
│  │   • top_k = 5                                          │     │
│  │   • score_threshold = 0.70                             │     │
│  │   • query_vector = [768-dim from query]                │     │
│  │                                                         │     │
│  │ Selected-Text Mode Parameters:                         │     │
│  │   • top_k = 3                                          │     │
│  │   • score_threshold = 0.85                             │     │
│  │   • query_vector = [768-dim from selected text]        │     │
│  │                                                         │     │
│  │ Search Process:                                         │     │
│  │   1. Compute cosine similarity: dot(query, stored)     │     │
│  │   2. Rank by similarity score (descending)             │     │
│  │   3. Filter by score_threshold                         │     │
│  │   4. Return top_k results                              │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 4: RESULT FORMATTING WITH METADATA                         │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Raw Qdrant Results:                                     │     │
│  │                                                         │     │
│  │ [                                                       │     │
│  │   ScoredPoint(                                          │     │
│  │     id="uuid-1",                                        │     │
│  │     score=0.89,                                         │     │
│  │     payload={                                           │     │
│  │       "text": "ROS 2 is...",                           │     │
│  │       "metadata": {                                     │     │
│  │         "chapter": "Getting Started",                  │     │
│  │         "section": "Introduction",                     │     │
│  │         "source_file": "intro.md",                     │     │
│  │         "chunk_index": 0,                              │     │
│  │         "total_chunks": 3,                             │     │
│  │         "token_count": 412                             │     │
│  │       }                                                 │     │
│  │     }                                                   │     │
│  │   )                                                     │     │
│  │ ]                                                       │     │
│  │                                                         │     │
│  │ ↓ Format to Standard Schema                            │     │
│  │                                                         │     │
│  │ Formatted Output:                                       │     │
│  │                                                         │     │
│  │ [                                                       │     │
│  │   {                                                     │     │
│  │     "text": "ROS 2 is...",                             │     │
│  │     "metadata": {                                       │     │
│  │       "chapter": "Getting Started",                    │     │
│  │       "section": "Introduction",                       │     │
│  │       "source_file": "intro.md",                       │     │
│  │       "chunk_index": 0,                                │     │
│  │       "total_chunks": 3,                               │     │
│  │       "token_count": 412                               │     │
│  │     },                                                  │     │
│  │     "score": 0.89                                      │     │
│  │   }                                                     │     │
│  │ ]                                                       │     │
│  │                                                         │     │
│  │ Quality Checks:                                         │     │
│  │   ✓ All required metadata fields present               │     │
│  │   ✓ Scores in descending order                         │     │
│  │   ✓ Text content not empty                             │     │
│  │   ✓ chunk_index < total_chunks                         │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 5: LOGGING & ERROR HANDLING                                │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Structured Logging:                                     │     │
│  │                                                         │     │
│  │ {                                                       │     │
│  │   "timestamp": "2026-01-03T12:00:00Z",                 │     │
│  │   "level": "INFO",                                      │     │
│  │   "phase": "retrieval",                                │     │
│  │   "event": "query_received",                           │     │
│  │   "query_length": 15,                                  │     │
│  │   "retrieval_mode": "normal",                          │     │
│  │   "has_selected_text": false                           │     │
│  │ }                                                       │     │
│  │                                                         │     │
│  │ {                                                       │     │
│  │   "timestamp": "2026-01-03T12:00:00.150Z",            │     │
│  │   "level": "INFO",                                      │     │
│  │   "phase": "embedding",                                │     │
│  │   "event": "embedding_generated",                      │     │
│  │   "embedding_dimension": 768,                          │     │
│  │   "latency_ms": 150                                    │     │
│  │ }                                                       │     │
│  │                                                         │     │
│  │ {                                                       │     │
│  │   "timestamp": "2026-01-03T12:00:00.400Z",            │     │
│  │   "level": "INFO",                                      │     │
│  │   "phase": "search",                                   │     │
│  │   "event": "qdrant_search_complete",                   │     │
│  │   "num_results": 5,                                    │     │
│  │   "top_score": 0.89,                                   │     │
│  │   "latency_ms": 250                                    │     │
│  │ }                                                       │     │
│  │                                                         │     │
│  │ Error Scenarios:                                        │     │
│  │                                                         │     │
│  │ • Empty query                                           │     │
│  │   → ValidationError: "Query cannot be empty"           │     │
│  │                                                         │     │
│  │ • Gemini quota exceeded                                 │     │
│  │   → Fallback to MockEmbeddings                         │     │
│  │   → Log warning: "Using mock embeddings (quota)"       │     │
│  │                                                         │     │
│  │ • Qdrant connection failure                             │     │
│  │   → Retry 3x with exponential backoff                  │     │
│  │   → If all fail: raise ConnectionError                 │     │
│  │                                                         │     │
│  │ • No results found                                      │     │
│  │   → Return empty list []                               │     │
│  │   → Log info: "No chunks above threshold"              │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ Output       │
│              │
│ List[Dict]:  │
│ [            │
│   {          │
│     "text": str,
│     "metadata": {
│       "chapter": str,
│       "section": str,
│       "source_file": str,
│       "chunk_index": int,
│       "total_chunks": int,
│       "token_count": int
│     },
│     "score": float
│   },
│   ...
│ ]            │
│              │
│ Ready for    │
│ RAG Agent    │
│ consumption  │
└──────────────┘
```

---

## Normal vs Selected-Text Mode Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                     NORMAL RETRIEVAL MODE                        │
└─────────────────────────────────────────────────────────────────┘

User Query: "What is ROS 2?"
      │
      ▼
Embed Query Text
      │
      ▼
Search Qdrant
• top_k = 5
• threshold = 0.70
      │
      ▼
Return 5 chunks
(diverse, broad context)


┌─────────────────────────────────────────────────────────────────┐
│                  SELECTED-TEXT RETRIEVAL MODE                    │
└─────────────────────────────────────────────────────────────────┘

User Query: "How does this work?"
Selected Text: "ROS 2 uses DDS for real-time communication"
      │
      ▼
Embed Selected Text (not query!)
      │
      ▼
Search Qdrant
• top_k = 3
• threshold = 0.85
      │
      ▼
Return 3 chunks
(highly similar to selection, narrow context)


┌─────────────────────────────────────────────────────────────────┐
│                         KEY DIFFERENCES                          │
└─────────────────────────────────────────────────────────────────┘

| Aspect | Normal | Selected-Text |
|--------|--------|---------------|
| What we embed | Query | Selected text |
| top_k | 5 | 3 |
| threshold | 0.70 | 0.85 |
| Goal | Broad coverage | Narrow precision |
| Use case | General question | Focus on passage |
```

---

## Data Flow with Timing

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIMING BREAKDOWN (P50)                        │
└─────────────────────────────────────────────────────────────────┘

t=0ms       User Query Received
            ↓
t=5ms       Input Validation Complete
            ↓
t=10ms      Embedding Request Sent to Gemini
            ↓
t=160ms     Embedding Received (150ms Gemini latency)
            ↓
t=165ms     Qdrant Search Initiated
            ↓
t=415ms     Qdrant Results Received (250ms search latency)
            ↓
t=420ms     Results Formatted
            ↓
t=425ms     Response Returned

Total Latency: ~425ms (P50)
            ~650ms (P95, with retry)

Breakdown:
• Input handling: 5ms
• Embedding generation: 150ms (Gemini API)
• Qdrant search: 250ms (vector search + network)
• Result formatting: 5ms
• Overhead: 15ms
```

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       MODULE STRUCTURE                           │
└─────────────────────────────────────────────────────────────────┘

retrieval/
├── __init__.py
│
├── config.py                    Configuration Management
│   ├── RetrievalConfig
│   │   ├── qdrant_url
│   │   ├── qdrant_api_key
│   │   ├── collection_name
│   │   ├── gemini_api_key
│   │   ├── normal_top_k = 5
│   │   ├── normal_threshold = 0.70
│   │   ├── selected_top_k = 3
│   │   └── selected_threshold = 0.85
│   └── load_config()
│
├── embeddings.py                Embedding Service
│   ├── EmbeddingService (ABC)
│   │   ├── embed_query(text) → List[float]
│   │   └── get_embedding_dimension() → int
│   │
│   ├── GeminiEmbeddings
│   │   ├── __init__(api_key)
│   │   ├── embed_query(text)
│   │   └── _handle_rate_limit()
│   │
│   └── get_embedding_service() → EmbeddingService
│       (Factory: returns Gemini or Mock)
│
├── qdrant_client.py            Qdrant Search Wrapper
│   └── QdrantRetriever
│       ├── __init__(url, api_key, collection)
│       ├── search(vector, k, threshold) → List[ScoredPoint]
│       ├── _format_results() → List[Dict]
│       ├── _validate_connection()
│       └── _retry_with_backoff()
│
├── retriever.py                Main Orchestrator
│   └── SemanticRetriever
│       ├── __init__(embedding_service, qdrant_client)
│       ├── retrieve(query, mode, selected_text) → List[Dict]
│       ├── _retrieve_normal(query) → List[Dict]
│       ├── _retrieve_selected_text(query, selection) → List[Dict]
│       ├── _validate_input()
│       └── _log_retrieval()
│
└── logger.py                   Structured Logging
    ├── setup_logger()
    ├── log_query_received()
    ├── log_embedding_generated()
    ├── log_search_complete()
    └── log_error()
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      ERROR HANDLING TREE                         │
└─────────────────────────────────────────────────────────────────┘

Retrieval Request
      │
      ├─ Empty Query?
      │     └─ YES → ValidationError("Query cannot be empty")
      │
      ├─ Selected-text mode but no selection?
      │     └─ YES → ValidationError("Selected text required")
      │
      ├─ Embedding Generation
      │     │
      │     ├─ Gemini quota exceeded?
      │     │     └─ YES → Fallback to MockEmbeddings
      │     │              Log warning
      │     │              Continue with mock
      │     │
      │     ├─ Network error?
      │     │     └─ YES → Retry 3x
      │     │              If fail → Raise EmbeddingError
      │     │
      │     └─ API key invalid?
      │           └─ YES → Raise AuthenticationError
      │
      ├─ Qdrant Search
      │     │
      │     ├─ Connection refused?
      │     │     └─ YES → Retry with exponential backoff
      │     │              1st: wait 1s
      │     │              2nd: wait 2s
      │     │              3rd: wait 4s
      │     │              If all fail → Raise ConnectionError
      │     │
      │     ├─ Collection not found?
      │     │     └─ YES → Raise CollectionNotFoundError
      │     │
      │     └─ No results above threshold?
      │           └─ YES → Return empty list []
      │                    Log info message
      │
      └─ Result Formatting
            │
            ├─ Missing metadata field?
            │     └─ YES → Log warning
            │              Use default value
            │              Continue
            │
            └─ Invalid score?
                  └─ YES → Log error
                           Skip chunk
                           Continue with remaining
```

---

## Quality Assurance Checkpoints

```
┌─────────────────────────────────────────────────────────────────┐
│                   QUALITY VALIDATION PIPELINE                    │
└─────────────────────────────────────────────────────────────────┘

Input Validation
├─ ✓ Query is not empty
├─ ✓ Query length < 1000 chars (reasonable limit)
├─ ✓ Selected text provided if mode="selected_text"
└─ ✓ Selected text length < 2000 chars

Embedding Validation
├─ ✓ Embedding dimension = 768
├─ ✓ All values are finite (no NaN, Inf)
├─ ✓ Vector is normalized (L2 norm ≈ 1.0)
└─ ✓ Same input → same embedding (determinism)

Search Validation
├─ ✓ Scores in range [0.0, 1.0]
├─ ✓ Scores in descending order
├─ ✓ All scores ≥ threshold
└─ ✓ Result count ≤ top_k

Metadata Integrity
├─ ✓ All chunks have required fields:
│   ├─ text (non-empty string)
│   ├─ chapter (non-empty string)
│   ├─ section (non-empty string)
│   ├─ source_file (non-empty string)
│   ├─ chunk_index (non-negative int)
│   ├─ total_chunks (positive int)
│   └─ token_count (positive int)
├─ ✓ chunk_index < total_chunks
└─ ✓ No duplicate chunks (by text hash)

Determinism Validation
├─ ✓ Query "X" at t1 → results R1
├─ ✓ Query "X" at t2 → results R2
├─ ✓ R1 == R2 (same chunks, same scores, same order)
└─ ✓ Repeated 3x to confirm consistency

Selected-Text Mode Validation
├─ ✓ Results are subset of normal mode results
├─ ✓ All results highly similar to selected text
├─ ✓ Result count ≤ selected_top_k (3)
└─ ✓ All scores ≥ selected_threshold (0.85)
```

---

## Performance Characteristics

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE PROFILE                           │
└─────────────────────────────────────────────────────────────────┘

Latency (Normal Mode):
┌────────────────────────────────────────┐
│ P50:  425ms                             │
│ P95:  650ms                             │
│ P99:  1200ms (with retries)            │
└────────────────────────────────────────┘

Latency Breakdown:
• Embedding: 150ms (35%)
• Qdrant search: 250ms (59%)
• Processing: 25ms (6%)

Throughput:
• Max: 15 requests/min (Gemini rate limit)
• Recommended: 10 requests/min (buffer for retries)

Memory Usage:
• Per request: ~10 KB
  ├─ Query embedding: 768 floats × 4 bytes = 3 KB
  ├─ Results (5 chunks): ~5 KB
  └─ Overhead: ~2 KB

Cache Efficiency (if enabled):
• Hit rate: 30-40% (repeated queries)
• Latency reduction: 150ms (skip embedding)
```

---

## Deployment Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────┘

Option A: Standalone Module
┌────────────────────────────────┐
│   Python Application            │
│                                 │
│   from retrieval import         │
│       SemanticRetriever         │
│                                 │
│   retriever = SemanticRetriever()│
│   results = retriever.retrieve()│
└────────────────────────────────┘
           │
           ├─────────────────┬──────────────────┐
           ▼                 ▼                  ▼
     ┌──────────┐      ┌──────────┐      ┌──────────┐
     │  Gemini  │      │  Qdrant  │      │   Logs   │
     │   API    │      │  Cloud   │      │  stdout  │
     └──────────┘      └──────────┘      └──────────┘


Option B: FastAPI Endpoint
┌────────────────────────────────┐
│   FastAPI Server (port 8001)   │
│                                 │
│   POST /retrieve                │
│   GET  /health                  │
└────────────────────────────────┘
           │
           ├─────────────────┬──────────────────┐
           ▼                 ▼                  ▼
     ┌──────────┐      ┌──────────┐      ┌──────────┐
     │  Gemini  │      │  Qdrant  │      │   Logs   │
     │   API    │      │  Cloud   │      │   File   │
     └──────────┘      └──────────┘      └──────────┘
```

---

**Last Updated**: 2026-01-03

**Status**: Architecture sketch complete

**Usage**: Reference this diagram during implementation to ensure all phases are correctly integrated
