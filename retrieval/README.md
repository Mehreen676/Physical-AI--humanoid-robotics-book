# Semantic Retrieval Layer

Standalone module for semantic search over book content in Qdrant.

## Features

- **Two retrieval modes**: Normal (broad) and Selected Text (constrained)
- **Swappable embeddings**: Gemini or Mock
- **Deterministic**: Same query → same results
- **Metadata preservation**: Chapter, section, source, chunks

## Quick Start

```python
from retrieval import SemanticRetriever

# Initialize
retriever = SemanticRetriever()

# Normal retrieval
results = retriever.retrieve(
    query="What is ROS 2?",
    retrieval_mode="normal"
)

# Selected text retrieval
results = retriever.retrieve(
    query="Explain this",
    retrieval_mode="selected_text",
    selected_text="ROS 2 uses DDS for communication"
)
```

## Environment Variables

```bash
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_api_key
COLLECTION_NAME=data_collection
GEMINI_API_KEY=your_gemini_key  # Optional if using mock
USE_MOCK_EMBEDDINGS=false
```

## Configuration

| Parameter | Normal Mode | Selected Text Mode |
|-----------|-------------|-------------------|
| top_k | 5 | 3 |
| threshold | 0.7 | 0.85 |

## Response Schema

```json
{
  "text": "chunk content",
  "metadata": {
    "chapter": "Chapter 1",
    "section": "Introduction",
    "source_file": "book.pdf",
    "chunk_index": 0,
    "total_chunks": 10,
    "token_count": 150
  },
  "score": 0.85
}
```

## Testing

```bash
# Run unit tests
pytest tests/test_embeddings.py

# Run integration tests
pytest tests/test_retrieval.py

# Quick validation
python test_retrieval_quick.py
```

## Architecture

```
Query → Embedding → Qdrant Search → Format → Results
         (Gemini)    (Cosine)        (Schema)
```

**Selected Text Mode**: Embeds selection (not query) for constrained retrieval.
