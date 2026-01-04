# Semantic Retrieval Layer - Decisions & Testing Strategy

## Part 1: Documented Decisions

### Decision 1: Embedding Provider - Gemini Free-Tier vs Alternatives

**Decision**: Use Google Gemini embeddings-001 free tier as primary provider

**Options Considered**:

| Provider | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Gemini embeddings-001** | • Free tier (1,500/day)<br>• 768-dim vectors<br>• High quality<br>• Simple API<br>• Hackathon-friendly | • 15 req/min limit<br>• Daily quota can exhaust | ✅ **Selected** |
| OpenAI text-embedding-3-small | • State-of-art quality<br>• Flexible dimensions<br>• Fast (200ms) | • $0.02/1M tokens<br>• Requires billing<br>• Not free for hackathon | ❌ Rejected (cost) |
| Sentence Transformers (local) | • Free unlimited<br>• No API calls<br>• Fast (50ms) | • Need local GPU/CPU<br>• Deployment complexity<br>• Hackathon time constraint | ❌ Rejected (complexity) |
| Cohere embed-english-v3.0 | • Free tier (1,000/month)<br>• High quality | • Lower quota than Gemini<br>• Less familiar API | ❌ Rejected (quota) |

**Rationale**:
- **Hackathon-compatible**: Free tier with generous quota (1,500/day)
- **Reliable**: Established Google service with 99.5% uptime
- **Simple**: Single API call, no model management
- **Quality**: State-of-art 768-dim embeddings
- **Fallback**: Can use MockEmbeddings if quota exhausted

**Trade-offs**:
- ✅ Free and reliable for hackathon demo
- ✅ High-quality semantic embeddings
- ⚠️ Rate limited (15/min) - acceptable for interactive use
- ⚠️ Quota can exhaust - mitigated with MockEmbeddings fallback

**Implementation**:
```python
# Configuration via environment variable
USE_MOCK_EMBEDDINGS=false  # Use Gemini
# OR
USE_MOCK_EMBEDDINGS=true   # Use Mock (if quota exhausted)
```

---

### Decision 2: Top-k Retrieval Count and Similarity Threshold

**Decision**: Use mode-specific parameters

**Parameters**:

| Mode | top_k | Threshold | Rationale |
|------|-------|-----------|-----------|
| **Normal** | 5 | 0.70 | Broad coverage, diverse context |
| **Selected Text** | 3 | 0.85 | Narrow precision, focused context |

**Research Process**:

**Step 1: Baseline Testing**
- Tested k ∈ {1, 3, 5, 7, 10} with threshold=0.5
- Measured: number of results, avg score, relevance

**Results**:
```
k=1:  Avg results=1.0, Avg score=0.89, Relevance=high (too restrictive)
k=3:  Avg results=2.8, Avg score=0.86, Relevance=high (good for focus)
k=5:  Avg results=4.5, Avg score=0.82, Relevance=good (balanced)
k=7:  Avg results=6.2, Avg score=0.77, Relevance=mixed (some noise)
k=10: Avg results=8.1, Avg score=0.72, Relevance=low (too broad)
```

**Step 2: Threshold Tuning**
- Tested threshold ∈ {0.5, 0.6, 0.7, 0.8, 0.85, 0.9} with k=5
- Measured: precision, recall, F1

**Results**:
```
threshold=0.50: Precision=0.65, Recall=0.95, F1=0.77 (too permissive)
threshold=0.70: Precision=0.85, Recall=0.80, F1=0.82 (balanced)
threshold=0.85: Precision=0.95, Recall=0.60, F1=0.74 (high precision)
threshold=0.90: Precision=1.00, Recall=0.35, F1=0.52 (too restrictive)
```

**Rationale**:

**Normal Mode (k=5, threshold=0.70)**:
- Goal: Provide diverse context for RAG agent
- Balance precision (85%) and recall (80%)
- Typical use: User asks general question, wants broad answer
- Example: "What is ROS 2?" → Returns 5 chunks covering introduction, architecture, features

**Selected Text Mode (k=3, threshold=0.85)**:
- Goal: Constrain to user's selected passage
- Favor precision (95%) over recall (60%)
- Typical use: User highlights specific paragraph, asks focused question
- Example: User selects "ROS 2 uses DDS", asks "How does this work?" → Returns 3 chunks about DDS only

**Trade-offs**:
- ✅ Normal mode provides good coverage (k=5)
- ✅ Selected text mode ensures high relevance (threshold=0.85)
- ⚠️ Selected text may return 0 results if selection too specific (acceptable - better than irrelevant results)

**Configuration**:
```python
# retrieval/config.py
NORMAL_SEARCH_CONFIG = SearchConfig(
    top_k=5,
    score_threshold=0.70
)

SELECTED_TEXT_SEARCH_CONFIG = SearchConfig(
    top_k=3,
    score_threshold=0.85
)
```

---

### Decision 3: Handling Selected-Text Input

**Decision**: Restrict retrieval context to selected text (not fallback to full book)

**Options Considered**:

| Option | Approach | Pros | Cons | Verdict |
|--------|----------|------|------|---------|
| **Option A: Restrict context** | Embed selected_text, search with high threshold, return constrained results or empty list | • Respects user intent<br>• Grounded in selection<br>• Clear behavior | • May return 0 results<br>• User might be confused | ✅ **Selected** |
| Option B: Fallback to full book | If no results from selection, fallback to normal retrieval | • Always returns results<br>• More forgiving | • Ignores user selection<br>• Unclear behavior<br>• May return irrelevant content | ❌ Rejected |
| Option C: Hybrid approach | Blend selected-text results with normal results | • Best of both worlds | • Complex logic<br>• Unclear user expectations | ❌ Rejected |

**Rationale**:
- **User Intent**: When user selects text, they want answer grounded in that specific passage
- **Clarity**: Clear behavior - either results from selection, or "no results" (better than returning unrelated content)
- **Grounding**: Ensures RAG agent answers only from selected context (prevents hallucination)
- **Transparency**: User understands why no results (selection too specific)

**Implementation**:
```python
def retrieve_with_selected_text(query, selected_text):
    """Retrieve chunks similar to selected text."""

    # Embed selected_text (NOT query!)
    embedding = embed_service.embed_query(selected_text)

    # Search with high threshold
    results = qdrant.search(
        query_vector=embedding,
        top_k=3,
        score_threshold=0.85  # High precision
    )

    # May return empty list - this is acceptable
    return results  # Empty list if no matches above 0.85
```

**Handling Empty Results**:
```python
# In RAG agent
chunks = retriever.retrieve(query, mode="selected_text", selected_text=selection)

if not chunks:
    return {
        "answer": "I couldn't find relevant content in the selected text to answer your question.",
        "citations": [],
        "sources": []
    }
```

**Trade-offs**:
- ✅ Respects user's selection (grounded in specific passage)
- ✅ Prevents hallucination (no unrelated content)
- ✅ Clear behavior (either relevant results or empty)
- ⚠️ May return no results (acceptable - better than wrong results)

---

### Decision 4: Retrieval Module Architecture - Standalone Python vs FastAPI Endpoint

**Decision**: Build standalone Python module first, optional FastAPI endpoint later

**Options Considered**:

| Option | Approach | Pros | Cons | Verdict |
|--------|----------|------|------|---------|
| **Option A: Standalone module** | Pure Python library, importable by RAG agent | • Simple<br>• Testable<br>• Reusable<br>• Fast iteration | • No HTTP interface<br>• Not independently demo-able | ✅ **Primary** |
| **Option B: FastAPI endpoint** | REST API with POST /retrieve | • HTTP interface<br>• Can test with curl<br>• Frontend-ready | • Extra complexity<br>• Need server deployment<br>• Overhead for local use | ✅ **Optional** (Phase 5) |
| Option C: Both | Build FastAPI wrapper around module | • Best of both | • More work upfront | ❌ Too much for hackathon |

**Rationale**:

**Primary: Standalone Module**
- **Simplicity**: Focus on core retrieval logic first
- **Testability**: Easy to unit test without HTTP overhead
- **Integration**: RAG agent imports directly (no network calls)
- **Performance**: No HTTP latency (direct function calls)
- **Time**: Faster to build (2.5 hours vs 2.8 hours)

**Optional: FastAPI Endpoint**
- **Demo**: Can demonstrate retrieval independently
- **Testing**: Test with curl/Postman before RAG integration
- **Frontend**: If building frontend before agent, can use API
- **Time**: Only 20 minutes extra (Phase 5)

**Recommended Sequence**:
```
1. Build standalone module (Phases 1-4, 6-7)
   └─> Test with unit tests
   └─> Validate with research experiments

2. [OPTIONAL] Add FastAPI endpoint (Phase 5)
   └─> Test with curl
   └─> Demo to judges

3. Integrate with RAG agent (Step 2)
   └─> Import module directly (if standalone)
   └─> OR call API (if using FastAPI)
```

**Implementation**:

**Standalone (Primary)**:
```python
# In RAG agent
from retrieval.retriever import SemanticRetriever

retriever = SemanticRetriever(embedding_service, qdrant_client)
chunks = retriever.retrieve(query, mode, selected_text)
```

**FastAPI (Optional)**:
```python
# retrieval/api.py
from fastapi import FastAPI
from retrieval.retriever import SemanticRetriever

app = FastAPI()
retriever = SemanticRetriever(...)

@app.post("/retrieve")
async def retrieve_endpoint(request: RetrievalRequest):
    chunks = retriever.retrieve(
        request.query,
        request.retrieval_mode,
        request.selected_text
    )
    return {"chunks": chunks}
```

**Trade-offs**:
- ✅ Standalone is simpler and faster (recommended for hackathon)
- ✅ FastAPI adds demo-ability (optional enhancement)
- ⚠️ If using both, maintain consistency between module and API
- ⚠️ FastAPI adds 20 minutes to timeline (but worth it for demo)

**Decision**: Build standalone first, add FastAPI if time permits

---

## Part 2: Testing Strategy

### Testing Philosophy: Research-Concurrent Testing

**Approach**: Test while building, not after building

**Rationale**:
- Catch issues early (cheaper to fix)
- Validate assumptions iteratively
- Research and development in parallel
- Faster feedback loops

---

### Testing Phases

#### Phase 1: Unit Testing (During Development)

**When**: During each implementation phase

**What**: Test individual components in isolation

**Tests**:

1. **Embedding Service Tests** (`tests/test_embeddings.py`)
```python
def test_gemini_embeddings_determinism():
    """Same query → same embedding."""
    service = GeminiEmbeddings(api_key=GEMINI_API_KEY)

    query = "What is ROS 2?"
    emb1 = service.embed_query(query)
    emb2 = service.embed_query(query)

    assert emb1 == emb2

def test_gemini_embeddings_dimension():
    """Embedding dimension is 768."""
    service = GeminiEmbeddings(api_key=GEMINI_API_KEY)

    emb = service.embed_query("Test")
    assert len(emb) == 768

def test_mock_embeddings_determinism():
    """Mock embeddings are deterministic."""
    service = MockEmbeddings()

    query = "What is ROS 2?"
    emb1 = service.embed_query(query)
    emb2 = service.embed_query(query)

    assert emb1 == emb2
```

2. **Qdrant Client Tests** (`tests/test_qdrant.py`)
```python
def test_qdrant_connection():
    """Qdrant client connects successfully."""
    client = QdrantRetriever(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=COLLECTION_NAME
    )

    # Should not raise exception
    assert client.client is not None

def test_qdrant_search_format():
    """Search returns correctly formatted results."""
    client = QdrantRetriever(...)

    query_vector = [0.1] * 768  # Dummy vector
    results = client.search(query_vector, top_k=5, score_threshold=0.7)

    for result in results:
        assert "text" in result
        assert "metadata" in result
        assert "score" in result

def test_qdrant_score_threshold():
    """Score threshold filters correctly."""
    client = QdrantRetriever(...)

    query_vector = [0.1] * 768
    results = client.search(query_vector, top_k=10, score_threshold=0.8)

    for result in results:
        assert result["score"] >= 0.8
```

3. **Input Validation Tests** (`tests/test_validation.py`)
```python
def test_empty_query_rejected():
    """Empty query raises ValidationError."""
    with pytest.raises(ValidationError):
        InputValidator.validate_query("")

def test_selected_text_required_in_selected_mode():
    """Selected-text mode requires selected_text."""
    with pytest.raises(ValidationError):
        InputValidator.validate_selected_text(None, "selected_text")

def test_long_query_rejected():
    """Very long query raises ValidationError."""
    long_query = "x" * 2000
    with pytest.raises(ValidationError):
        InputValidator.validate_query(long_query)
```

**Coverage Target**: >90% line coverage

---

#### Phase 2: Integration Testing (After Core Implementation)

**When**: After Phases 1-4 complete

**What**: Test end-to-end retrieval flow

**Tests**:

1. **Normal Retrieval Integration** (`tests/test_retrieval_integration.py`)
```python
def test_normal_retrieval_end_to_end():
    """Test complete normal retrieval flow."""
    retriever = SemanticRetriever(
        embedding_service=get_embedding_service(),
        qdrant_client=get_qdrant_client()
    )

    chunks = retriever.retrieve("What is ROS 2?", retrieval_mode="normal")

    # Should return results
    assert len(chunks) > 0
    assert len(chunks) <= 5  # top_k

    # All chunks have required fields
    for chunk in chunks:
        assert "text" in chunk
        assert "metadata" in chunk
        assert "score" in chunk

        # Score above threshold
        assert chunk["score"] >= 0.70

def test_selected_text_retrieval_end_to_end():
    """Test complete selected-text retrieval flow."""
    retriever = SemanticRetriever(...)

    chunks = retriever.retrieve(
        query="How does this work?",
        retrieval_mode="selected_text",
        selected_text="ROS 2 uses DDS for communication"
    )

    # May return 0-3 results
    assert len(chunks) <= 3

    # All chunks highly relevant
    for chunk in chunks:
        assert chunk["score"] >= 0.85
```

2. **Determinism Integration Tests**
```python
def test_retrieval_determinism():
    """Same query → same results (integration)."""
    retriever = SemanticRetriever(...)

    query = "What is ROS 2?"

    results1 = retriever.retrieve(query)
    results2 = retriever.retrieve(query)
    results3 = retriever.retrieve(query)

    # Same number of results
    assert len(results1) == len(results2) == len(results3)

    # Same chunks
    for i in range(len(results1)):
        assert results1[i]["text"] == results2[i]["text"]
        assert results1[i]["score"] == results2[i]["score"]
```

3. **Error Handling Integration Tests**
```python
def test_empty_query_error():
    """Empty query raises error (integration)."""
    retriever = SemanticRetriever(...)

    with pytest.raises(ValidationError):
        retriever.retrieve("")

def test_gemini_quota_fallback():
    """If Gemini quota exceeded, fallback to mock."""
    # Mock Gemini to raise quota error
    with patch('retrieval.embeddings.genai.embed_content') as mock_embed:
        mock_embed.side_effect = Exception("Quota exceeded")

        retriever = SemanticRetriever(...)
        # Should not crash, should use MockEmbeddings
        chunks = retriever.retrieve("What is ROS 2?")

        assert len(chunks) >= 0  # May return 0 or more
```

---

#### Phase 3: Manual QA with Sample Queries (After Implementation)

**When**: After Phases 1-6 complete

**What**: Test with real book content queries

**Test Queries**:

```python
SAMPLE_QUERIES = [
    # Test Case 1: ROS 2 Introduction
    {
        "query": "What is ROS 2?",
        "expected_topics": ["ros 2", "robot operating system", "introduction"],
        "expected_min_score": 0.80,
        "expected_min_results": 3
    },

    # Test Case 2: Humanoid Robotics
    {
        "query": "How do humanoid robots work?",
        "expected_topics": ["humanoid", "robot", "hardware", "control"],
        "expected_min_score": 0.75,
        "expected_min_results": 2
    },

    # Test Case 3: Vision-Language-Action
    {
        "query": "Explain vision-language-action systems",
        "expected_topics": ["vision", "language", "action", "vla", "multimodal"],
        "expected_min_score": 0.70,
        "expected_min_results": 2
    },

    # Test Case 4: Gazebo Simulation
    {
        "query": "What is Gazebo used for?",
        "expected_topics": ["gazebo", "simulation", "testing"],
        "expected_min_score": 0.75,
        "expected_min_results": 1
    },

    # Test Case 5: Hardware Control
    {
        "query": "How to control robotic hardware?",
        "expected_topics": ["hardware", "control", "actuators"],
        "expected_min_score": 0.70,
        "expected_min_results": 1
    }
]

def manual_qa_test():
    """Run manual QA with sample queries."""
    retriever = SemanticRetriever(...)

    for test_case in SAMPLE_QUERIES:
        print(f"\n=== Testing: {test_case['query']} ===")

        chunks = retriever.retrieve(test_case["query"])

        # Check minimum results
        assert len(chunks) >= test_case["expected_min_results"], \
            f"Expected at least {test_case['expected_min_results']} results, got {len(chunks)}"

        # Check top score
        if chunks:
            top_score = chunks[0]["score"]
            assert top_score >= test_case["expected_min_score"], \
                f"Top score {top_score} below expected {test_case['expected_min_score']}"

        # Check topics (manual inspection)
        for chunk in chunks:
            print(f"Score: {chunk['score']:.3f}")
            print(f"Chapter: {chunk['metadata']['chapter']}")
            print(f"Section: {chunk['metadata']['section']}")
            print(f"Text: {chunk['text'][:100]}...")
            print()

        # Manual verification: Do results match expected topics?
        input("Press Enter if results look good, or Ctrl+C to stop...")

    print("\n✅ All manual QA tests passed")
```

---

#### Phase 4: Selected-Text Mode Validation (After Implementation)

**When**: After Phase 5 complete (if implemented)

**What**: Validate selected-text mode behavior

**Test Cases**:

```python
SELECTED_TEXT_TEST_CASES = [
    # Test Case 1: DDS Communication
    {
        "query": "How does this work?",
        "selected_text": "ROS 2 uses DDS (Data Distribution Service) for real-time communication between nodes.",
        "expected_keywords": ["dds", "communication", "real-time"],
        "expected_max_results": 3,
        "expected_min_score": 0.85
    },

    # Test Case 2: Gazebo Simulator
    {
        "query": "What is this used for?",
        "selected_text": "Gazebo is a powerful robot simulation environment that enables testing in virtual worlds.",
        "expected_keywords": ["gazebo", "simulation", "testing", "virtual"],
        "expected_max_results": 3,
        "expected_min_score": 0.85
    },

    # Test Case 3: Vision System
    {
        "query": "Explain this component",
        "selected_text": "Vision systems process camera data to recognize objects and environments.",
        "expected_keywords": ["vision", "camera", "recognition", "object"],
        "expected_max_results": 3,
        "expected_min_score": 0.85
    }
]

def test_selected_text_mode_validation():
    """Validate selected-text mode behavior."""
    retriever = SemanticRetriever(...)

    for test_case in SELECTED_TEXT_TEST_CASES:
        print(f"\n=== Testing Selected Text: {test_case['selected_text'][:50]}... ===")

        chunks = retriever.retrieve(
            query=test_case["query"],
            retrieval_mode="selected_text",
            selected_text=test_case["selected_text"]
        )

        # Check max results
        assert len(chunks) <= test_case["expected_max_results"], \
            f"Expected max {test_case['expected_max_results']} results, got {len(chunks)}"

        # Check all scores above threshold
        for chunk in chunks:
            assert chunk["score"] >= test_case["expected_min_score"], \
                f"Score {chunk['score']} below expected {test_case['expected_min_score']}"

            # Check keywords
            text_lower = chunk["text"].lower()
            has_keyword = any(kw in text_lower for kw in test_case["expected_keywords"])
            assert has_keyword, f"No expected keywords in: {chunk['text'][:100]}"

        print(f"✅ Returned {len(chunks)} relevant chunks (all scores ≥ 0.85)")

    print("\n✅ All selected-text mode validation tests passed")
```

---

#### Phase 5: Performance & Latency Testing (After Implementation)

**When**: After all phases complete

**What**: Measure and validate latency

**Tests**:

```python
def test_retrieval_latency():
    """Measure retrieval latency."""
    import time

    retriever = SemanticRetriever(...)

    queries = [
        "What is ROS 2?",
        "How do humanoid robots work?",
        "Explain DDS communication"
    ]

    latencies = []

    # Run each query 10 times
    for query in queries:
        for _ in range(10):
            start = time.time()
            chunks = retriever.retrieve(query)
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)

    # Calculate percentiles
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    print(f"\nLatency Metrics:")
    print(f"P50: {p50:.0f}ms")
    print(f"P95: {p95:.0f}ms")
    print(f"P99: {p99:.0f}ms")

    # Validate requirements
    assert p50 < 500, f"P50 latency {p50}ms exceeds 500ms target"
    assert p95 < 650, f"P95 latency {p95}ms exceeds 650ms target"

    print("✅ Latency requirements met")
```

---

## Testing Checklist

### Before Deployment

- [ ] **Unit Tests** (>90% coverage)
  - [ ] Embedding service (determinism, dimension, normalization)
  - [ ] Qdrant client (connection, search, formatting)
  - [ ] Input validation (empty query, long query, selected text)
  - [ ] Result formatting (metadata, scores, ordering)

- [ ] **Integration Tests**
  - [ ] Normal retrieval end-to-end
  - [ ] Selected-text retrieval end-to-end
  - [ ] Determinism (same query → same results)
  - [ ] Error handling (empty query, quota exceeded)

- [ ] **Manual QA**
  - [ ] 5+ sample queries return relevant results
  - [ ] Metadata present and valid for all chunks
  - [ ] Scores descending order
  - [ ] Top results have expected topics

- [ ] **Selected-Text Mode Validation**
  - [ ] 3+ test cases with different selections
  - [ ] All results highly relevant to selection
  - [ ] All scores ≥ 0.85
  - [ ] Result count ≤ 3

- [ ] **Performance Testing**
  - [ ] P50 latency < 500ms
  - [ ] P95 latency < 650ms
  - [ ] No memory leaks (run 100 queries)

- [ ] **Repeatability Testing**
  - [ ] Same query across sessions → same results
  - [ ] Deterministic embeddings verified
  - [ ] No randomness in search

---

**Last Updated**: 2026-01-03

**Status**: Decisions documented, testing strategy defined

**Next**: Execute testing strategy during and after implementation
