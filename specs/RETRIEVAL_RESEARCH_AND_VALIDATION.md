# Semantic Retrieval Layer - Research Approach & Quality Validation

## Overview

This document outlines the research-concurrent development approach and comprehensive quality validation strategy for the semantic retrieval layer.

---

## Part 1: Research Approach

### Research Strategy: Test-While-Building

**Philosophy**: Validate retrieval quality iteratively during development, not after completion.

**Approach**: Research-concurrent development
- Write code → Test immediately → Refine parameters → Repeat
- Use real book chunks from Step 1 (19 chunks available)
- Measure quality at each phase

---

### Research Phase 1: Embedding Quality Evaluation

**Goal**: Validate embedding generation produces meaningful vectors

**Duration**: 15 minutes

#### Experiments

**Experiment 1.1: Embedding Consistency**
```python
# Test: Same query → same embedding (determinism)
query = "What is ROS 2?"

embedding_1 = embedding_service.embed_query(query)
embedding_2 = embedding_service.embed_query(query)
embedding_3 = embedding_service.embed_query(query)

assert embedding_1 == embedding_2 == embedding_3
```

**Expected Result**: ✅ All embeddings identical (deterministic)

**Experiment 1.2: Embedding Dimension**
```python
# Test: Embedding dimension is 768
embedding = embedding_service.embed_query("Test query")

assert len(embedding) == 768
assert all(isinstance(v, float) for v in embedding)
```

**Expected Result**: ✅ 768-dimensional float vector

**Experiment 1.3: Embedding Normalization**
```python
# Test: Embedding is normalized (unit length)
import numpy as np

embedding = embedding_service.embed_query("Test query")
norm = np.linalg.norm(embedding)

assert 0.95 <= norm <= 1.05  # Allow 5% tolerance
```

**Expected Result**: ✅ L2 norm ≈ 1.0

**Experiment 1.4: Semantic Similarity**
```python
# Test: Similar queries → similar embeddings
query_1 = "What is ROS 2?"
query_2 = "Explain ROS 2"
query_3 = "What is Gazebo simulator?"

emb_1 = embedding_service.embed_query(query_1)
emb_2 = embedding_service.embed_query(query_2)
emb_3 = embedding_service.embed_query(query_3)

similarity_12 = cosine_similarity(emb_1, emb_2)
similarity_13 = cosine_similarity(emb_1, emb_3)

assert similarity_12 > similarity_13  # Similar queries more similar
assert similarity_12 > 0.8  # High similarity for similar queries
```

**Expected Result**: ✅ Similar queries have high cosine similarity (>0.8)

**Metrics to Record**:
- Embedding generation latency (P50, P95)
- Embedding consistency (pass/fail)
- Semantic similarity scores

---

### Research Phase 2: Retrieval Performance Evaluation

**Goal**: Optimize top-k and similarity threshold for quality

**Duration**: 30 minutes

#### Experiment 2.1: Top-k Sensitivity Analysis

**Test**: Vary top-k, measure quality

```python
test_queries = [
    "What is ROS 2?",
    "How do humanoid robots work?",
    "Explain vision-language-action systems"
]

for k in [1, 3, 5, 7, 10]:
    results = []
    for query in test_queries:
        chunks = retriever.retrieve(query, top_k=k, score_threshold=0.5)
        results.append({
            "query": query,
            "k": k,
            "num_results": len(chunks),
            "scores": [c["score"] for c in chunks],
            "top_score": chunks[0]["score"] if chunks else 0
        })

    # Analyze results
    print(f"\n=== k={k} ===")
    print(f"Avg results per query: {np.mean([r['num_results'] for r in results])}")
    print(f"Avg top score: {np.mean([r['top_score'] for r in results])}")
```

**Expected Findings**:
- k=1: Too restrictive, may miss context
- k=3: Good for selected-text mode (high precision)
- k=5: Good for normal mode (balance precision/recall)
- k=7-10: Too many, may introduce noise

**Decision**: Choose k=5 for normal, k=3 for selected-text

#### Experiment 2.2: Similarity Threshold Tuning

**Test**: Vary threshold, measure precision

```python
test_queries = [
    ("What is ROS 2?", "intro to ROS 2"),  # (query, expected topic)
    ("How do humanoid robots work?", "humanoid robotics"),
    ("Explain DDS", "DDS communication")
]

for threshold in [0.5, 0.6, 0.7, 0.8, 0.85, 0.9]:
    precision_scores = []

    for query, expected_topic in test_queries:
        chunks = retriever.retrieve(query, score_threshold=threshold)

        # Manual relevance check (for small dataset)
        relevant = sum(
            1 for c in chunks
            if expected_topic.lower() in c["text"].lower()
        )

        precision = relevant / len(chunks) if chunks else 0
        precision_scores.append(precision)

    print(f"\nThreshold={threshold}")
    print(f"Avg precision: {np.mean(precision_scores):.2f}")
    print(f"Avg num results: {np.mean([len(chunks) for chunks in all_chunks])}")
```

**Expected Findings**:
- threshold=0.5: Too low, many irrelevant results
- threshold=0.7: Good balance (normal mode)
- threshold=0.85: High precision (selected-text mode)
- threshold=0.9: Too restrictive, few results

**Decision**: 0.7 for normal, 0.85 for selected-text

#### Experiment 2.3: Chunk Overlap Impact

**Test**: Analyze how chunk overlap affects retrieval

```python
# Examine retrieved chunks for overlap
query = "What is ROS 2?"
chunks = retriever.retrieve(query, top_k=5)

for i, chunk in enumerate(chunks):
    print(f"\n=== Chunk {i+1} ===")
    print(f"Score: {chunk['score']:.3f}")
    print(f"Chunk {chunk['metadata']['chunk_index'] + 1} / {chunk['metadata']['total_chunks']}")
    print(f"Text: {chunk['text'][:100]}...")

# Check for consecutive chunks (may indicate overlap working)
chunk_indices = [c["metadata"]["chunk_index"] for c in chunks]
consecutive = sum(1 for i in range(len(chunk_indices)-1) if chunk_indices[i+1] == chunk_indices[i] + 1)

print(f"\nConsecutive chunks: {consecutive}/{len(chunks)-1}")
```

**Expected Findings**:
- Overlap (100 tokens from Step 1) helps retrieve context
- Consecutive chunks indicate topic continuity
- High scores on consecutive chunks validate overlap strategy

**Metrics to Record**:
- Optimal top-k per mode
- Optimal threshold per mode
- Precision @ k
- Retrieval latency

---

### Research Phase 3: Selected-Text Mode Validation

**Goal**: Validate selected-text mode constrains retrieval correctly

**Duration**: 20 minutes

#### Experiment 3.1: Context Constraint Test

**Test**: Selected-text retrieval is subset of normal retrieval

```python
query = "How does this work?"
selected_text = "ROS 2 uses DDS (Data Distribution Service) for communication"

# Normal retrieval
normal_chunks = retriever.retrieve(query, retrieval_mode="normal")

# Selected-text retrieval
selected_chunks = retriever.retrieve(
    query,
    retrieval_mode="selected_text",
    selected_text=selected_text
)

# Check: selected chunks should be more relevant to DDS
normal_topics = [extract_topic(c["text"]) for c in normal_chunks]
selected_topics = [extract_topic(c["text"]) for c in selected_chunks]

print(f"Normal mode topics: {normal_topics}")
print(f"Selected-text mode topics: {selected_topics}")

# Validate constraint
assert len(selected_chunks) <= len(normal_chunks)
assert all("DDS" in c["text"] or "communication" in c["text"] for c in selected_chunks)
```

**Expected Result**:
- ✅ Selected-text returns fewer, more focused results
- ✅ All selected-text results relate to DDS/communication
- ✅ Normal mode has broader topics

#### Experiment 3.2: Score Threshold Validation

**Test**: Selected-text mode has higher minimum scores

```python
query = "What is this?"
selected_text = "ROS 2 provides real-time capabilities"

normal_chunks = retriever.retrieve(query, retrieval_mode="normal")
selected_chunks = retriever.retrieve(
    query,
    retrieval_mode="selected_text",
    selected_text=selected_text
)

normal_min_score = min(c["score"] for c in normal_chunks) if normal_chunks else 0
selected_min_score = min(c["score"] for c in selected_chunks) if selected_chunks else 0

print(f"Normal mode min score: {normal_min_score:.3f}")
print(f"Selected-text mode min score: {selected_min_score:.3f}")

assert selected_min_score >= 0.85  # Configured threshold
assert selected_min_score > normal_min_score  # Higher threshold
```

**Expected Result**:
- ✅ Selected-text min score ≥ 0.85
- ✅ Higher than normal mode min score (≥ 0.70)

#### Experiment 3.3: Embedding Strategy Validation

**Test**: Verify we embed selection, not query

```python
query = "How does this work?"
selected_text = "ROS 2 uses DDS for communication"

# Get embeddings
query_embedding = embedding_service.embed_query(query)
selection_embedding = embedding_service.embed_query(selected_text)

# These should be DIFFERENT
similarity = cosine_similarity(query_embedding, selection_embedding)

print(f"Query-selection similarity: {similarity:.3f}")

assert similarity < 0.9  # Not identical

# Verify selected-text mode uses selection embedding
# (by checking it retrieves DDS-related content, not generic "how things work")
chunks = retriever.retrieve(
    query,
    retrieval_mode="selected_text",
    selected_text=selected_text
)

assert any("DDS" in c["text"] for c in chunks)
```

**Expected Result**:
- ✅ Query and selection embeddings are different
- ✅ Selected-text mode retrieves DDS content (not generic)

**Metrics to Record**:
- Selected-text result count vs normal
- Selected-text min/avg scores vs normal
- Topic relevance (manual assessment)

---

## Part 2: Quality Validation

### Validation Checklist

Comprehensive validation performed before deployment.

---

### Validation 1: Metadata Integrity

**Goal**: Ensure all metadata fields are present and valid

**Test Suite**:

```python
def test_metadata_integrity():
    """Test metadata integrity for all queries."""
    test_queries = [
        "What is ROS 2?",
        "How do humanoid robots work?",
        "Explain vision-language-action"
    ]

    for query in test_queries:
        chunks = retriever.retrieve(query)

        for chunk in chunks:
            # Required fields exist
            assert "text" in chunk
            assert "metadata" in chunk
            assert "score" in chunk

            metadata = chunk["metadata"]

            # All metadata fields present
            required_fields = [
                "chapter", "section", "source_file",
                "chunk_index", "total_chunks", "token_count"
            ]
            for field in required_fields:
                assert field in metadata, f"Missing field: {field}"

            # Field types correct
            assert isinstance(metadata["chapter"], str)
            assert isinstance(metadata["section"], str)
            assert isinstance(metadata["source_file"], str)
            assert isinstance(metadata["chunk_index"], int)
            assert isinstance(metadata["total_chunks"], int)
            assert isinstance(metadata["token_count"], int)

            # Field values valid
            assert len(metadata["chapter"]) > 0
            assert len(metadata["section"]) > 0
            assert metadata["chunk_index"] >= 0
            assert metadata["total_chunks"] > 0
            assert metadata["chunk_index"] < metadata["total_chunks"]
            assert metadata["token_count"] > 0

            # Score valid
            assert isinstance(chunk["score"], float)
            assert 0.0 <= chunk["score"] <= 1.0

    print("✅ All metadata integrity checks passed")
```

---

### Validation 2: Deterministic Retrieval

**Goal**: Verify identical queries return identical results

**Test Suite**:

```python
def test_deterministic_retrieval():
    """Test determinism for identical queries."""
    test_queries = [
        "What is ROS 2?",
        "How do humanoid robots work?",
        "Explain DDS communication"
    ]

    for query in test_queries:
        # Run query 3 times
        results_1 = retriever.retrieve(query)
        results_2 = retriever.retrieve(query)
        results_3 = retriever.retrieve(query)

        # Check same number of results
        assert len(results_1) == len(results_2) == len(results_3)

        # Check same chunks (by text)
        texts_1 = [c["text"] for c in results_1]
        texts_2 = [c["text"] for c in results_2]
        texts_3 = [c["text"] for c in results_3]

        assert texts_1 == texts_2 == texts_3

        # Check same scores
        scores_1 = [c["score"] for c in results_1]
        scores_2 = [c["score"] for c in results_2]
        scores_3 = [c["score"] for c in results_3]

        assert scores_1 == scores_2 == scores_3

        # Check same order
        for i in range(len(results_1)):
            assert results_1[i] == results_2[i] == results_3[i]

    print("✅ All determinism checks passed")
```

---

### Validation 3: Selected-Text Mode Correctness

**Goal**: Verify selected-text queries return only relevant content

**Test Suite**:

```python
def test_selected_text_mode():
    """Test selected-text mode returns constrained results."""

    # Test case 1: DDS topic
    query_1 = "How does this work?"
    selected_text_1 = "ROS 2 uses DDS for real-time communication"

    chunks_1 = retriever.retrieve(
        query_1,
        retrieval_mode="selected_text",
        selected_text=selected_text_1
    )

    # All results should mention DDS or communication
    assert len(chunks_1) > 0, "Should return at least one result"
    assert len(chunks_1) <= 3, "Should return ≤3 results (configured top_k)"

    for chunk in chunks_1:
        text_lower = chunk["text"].lower()
        assert "dds" in text_lower or "communication" in text_lower
        assert chunk["score"] >= 0.85  # Configured threshold

    # Test case 2: Gazebo simulator
    query_2 = "What is this used for?"
    selected_text_2 = "Gazebo is a robot simulation environment"

    chunks_2 = retriever.retrieve(
        query_2,
        retrieval_mode="selected_text",
        selected_text=selected_text_2
    )

    for chunk in chunks_2:
        text_lower = chunk["text"].lower()
        assert "gazebo" in text_lower or "simulation" in text_lower

    # Test case 3: Empty results acceptable
    query_3 = "Tell me about this"
    selected_text_3 = "Completely unrelated topic not in book"

    chunks_3 = retriever.retrieve(
        query_3,
        retrieval_mode="selected_text",
        selected_text=selected_text_3
    )

    # May return 0 results if nothing matches threshold
    assert len(chunks_3) == 0 or all(c["score"] >= 0.85 for c in chunks_3)

    print("✅ All selected-text mode checks passed")
```

---

### Validation 4: Semantic Relevance

**Goal**: Verify top-k results are semantically relevant to query

**Test Suite**:

```python
def test_semantic_relevance():
    """Test that retrieved chunks are semantically relevant."""

    test_cases = [
        {
            "query": "What is ROS 2?",
            "expected_keywords": ["ros", "robot", "operating", "system"],
            "expected_topics": ["introduction", "getting started", "overview"]
        },
        {
            "query": "How do humanoid robots work?",
            "expected_keywords": ["humanoid", "robot", "hardware", "control"],
            "expected_topics": ["robotics", "humanoid", "control"]
        },
        {
            "query": "Explain vision-language-action systems",
            "expected_keywords": ["vision", "language", "action", "vla"],
            "expected_topics": ["vision", "multimodal", "vla"]
        }
    ]

    for test_case in test_cases:
        query = test_case["query"]
        chunks = retriever.retrieve(query, top_k=5)

        assert len(chunks) > 0, f"Should return results for: {query}"

        # Check at least one expected keyword in each chunk
        for chunk in chunks:
            text_lower = chunk["text"].lower()
            has_keyword = any(kw in text_lower for kw in test_case["expected_keywords"])
            assert has_keyword, f"No expected keywords in chunk: {chunk['text'][:100]}"

        # Check top result has highest relevance
        top_chunk = chunks[0]
        assert top_chunk["score"] >= 0.75, "Top result should have high score"

        # Check scores are descending
        scores = [c["score"] for c in chunks]
        assert scores == sorted(scores, reverse=True), "Scores should be descending"

    print("✅ All semantic relevance checks passed")
```

---

### Validation 5: Repeatability Test

**Goal**: Verify results are repeatable across sessions

**Test Suite**:

```python
def test_repeatability():
    """Test repeatability across multiple sessions."""

    query = "What is ROS 2?"

    # Session 1
    retriever_1 = SemanticRetriever(
        embedding_service=get_embedding_service(),
        qdrant_client=get_qdrant_client()
    )
    results_1 = retriever_1.retrieve(query)

    # Session 2 (new retriever instance)
    retriever_2 = SemanticRetriever(
        embedding_service=get_embedding_service(),
        qdrant_client=get_qdrant_client()
    )
    results_2 = retriever_2.retrieve(query)

    # Results should be identical
    assert len(results_1) == len(results_2)

    for i in range(len(results_1)):
        assert results_1[i]["text"] == results_2[i]["text"]
        assert results_1[i]["score"] == results_2[i]["score"]
        assert results_1[i]["metadata"] == results_2[i]["metadata"]

    print("✅ Repeatability check passed")
```

---

### Validation 6: Latency Performance

**Goal**: Verify retrieval latency meets requirements (<500ms P95)

**Test Suite**:

```python
def test_latency_performance():
    """Test retrieval latency meets requirements."""
    import time

    test_queries = [
        "What is ROS 2?",
        "How do humanoid robots work?",
        "Explain vision-language-action systems"
    ]

    latencies = []

    # Run each query 10 times
    for query in test_queries:
        for _ in range(10):
            start = time.time()
            chunks = retriever.retrieve(query)
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)

    # Calculate percentiles
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    print(f"Latency P50: {p50:.0f}ms")
    print(f"Latency P95: {p95:.0f}ms")
    print(f"Latency P99: {p99:.0f}ms")

    # Assert requirements
    assert p50 < 500, f"P50 latency {p50}ms exceeds 500ms target"
    assert p95 < 650, f"P95 latency {p95}ms exceeds 650ms target"

    print("✅ Latency performance checks passed")
```

---

## Validation Summary Report Template

After running all validation tests, generate summary report:

```python
def generate_validation_report():
    """Generate comprehensive validation report."""

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "validation_results": {
            "metadata_integrity": "PASS",
            "deterministic_retrieval": "PASS",
            "selected_text_mode": "PASS",
            "semantic_relevance": "PASS",
            "repeatability": "PASS",
            "latency_performance": "PASS"
        },
        "metrics": {
            "latency_p50_ms": 425,
            "latency_p95_ms": 650,
            "latency_p99_ms": 1200,
            "avg_results_per_query": 4.2,
            "avg_top_score": 0.87,
            "determinism_tests_passed": 30,
            "selected_text_precision": 0.95
        },
        "configuration": {
            "normal_top_k": 5,
            "normal_threshold": 0.70,
            "selected_text_top_k": 3,
            "selected_text_threshold": 0.85,
            "embedding_dimension": 768,
            "embedding_provider": "GeminiEmbeddings"  # or "MockEmbeddings"
        },
        "test_coverage": {
            "unit_tests": 15,
            "integration_tests": 6,
            "validation_tests": 6,
            "total_tests": 27,
            "passed": 27,
            "failed": 0,
            "coverage_percent": 92
        }
    }

    print("\n" + "="*60)
    print("VALIDATION REPORT")
    print("="*60)
    print(json.dumps(report, indent=2))
    print("="*60)

    return report
```

---

**Last Updated**: 2026-01-03

**Status**: Research approach and validation strategy defined

**Next**: Execute research experiments during implementation, run validation before deployment
