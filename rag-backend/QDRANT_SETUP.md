# Qdrant Cloud Integration Guide

## Overview

This backend uses **Qdrant Cloud** (free tier) for vector storage and semantic similarity search. Qdrant provides a serverless vector database perfect for RAG applications.

## Setup Steps

### 1. Create Qdrant Cloud Account

1. Visit [https://cloud.qdrant.io](https://cloud.qdrant.io)
2. Sign up for a free account (no credit card required)
3. Create a new cluster (free tier provides 1GB storage)
4. Wait for cluster to be ready (~2-5 minutes)

### 2. Get API Credentials

From the Qdrant Cloud dashboard:

1. Go to **Cluster Details**
2. Copy your **Cluster URL** (e.g., `https://xxx-xxx-xxx.qdrant.io`)
3. Copy your **API Key** from the **Configuration** section

### 3. Update Environment Variables

Add to `.env` file:

```env
QDRANT_URL=https://1226c5c9-c8a8-4a11-aa69-0166c93ba368.europe-west3-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=sk-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.KnMZXZZ-ritUFBpl2OVASfgKEjm4J1F07XqI-r5goHc
QDRANT_COLLECTION_NAME=book_v1.0_chapters
```

### 4. Test Connection

```python
from vector_store import get_vector_store

store = get_vector_store()
info = store.get_collection_info()
print(info)
# Output: {name: 'book_v1.0_chapters', points_count: 0, ...}
```

## Vector Store API

### Create Collection

```python
store = get_vector_store()
store.create_collection()
```

### Store Single Vector

```python
vector_id = "doc_chunk_001"
embedding = [0.1, 0.2, ..., 0.15]  # 1536 dimensions
metadata = {
    "chapter": "Module 1: ROS 2",
    "section": "Basics",
    "content": "ROS 2 is a robotics middleware...",
    "doc_id": "doc_001",
    "chunk_index": 0
}

store.store_vector(vector_id, embedding, metadata)
```

### Store Vectors in Batch

```python
vectors_data = [
    ("id_1", embedding_1, metadata_1),
    ("id_2", embedding_2, metadata_2),
    ("id_3", embedding_3, metadata_3),
]

count = store.store_vectors_batch(vectors_data)
print(f"Stored {count} vectors")
```

### Search by Semantic Similarity

```python
query_embedding = [0.15, 0.25, ..., 0.12]  # 1536 dimensions

# Get top 5 most similar chunks
results = store.query_vectors(query_embedding, k=5)

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Chapter: {result['chapter']}")
    print(f"Content: {result['content'][:100]}...")
```

### Search with Filters

```python
filters = {"chapter": "Module 1: ROS 2"}
results = store.query_vectors(query_embedding, k=5, filters=filters)
```

### Get Collection Statistics

```python
info = store.get_collection_info()
# {
#   'name': 'book_v1.0_chapters',
#   'points_count': 1523,
#   'vector_size': 1536,
#   'distance_metric': 'cosine'
# }
```

## Storage Limits

**Free Tier**:
- 1 GB storage
- ~15,000 vectors (1536-dim, with metadata)
- Full API access

**Scaling**:
- For >1GB: Upgrade to paid tier (~$0.10/GB/month)
- At typical usage (500-1000 queries/month), free tier is sufficient for v1.0

## Performance

**Latency Benchmarks** (empirical):
- Vector insertion: ~100ms
- Query (top-5): ~50-150ms (p95 < 500ms)
- Batch insert (100 vectors): ~500ms

**Optimization Tips**:
- Use batch insert for multiple vectors (faster than individual inserts)
- Filter by metadata to reduce search space
- Regularly monitor collection size via dashboard

## Troubleshooting

### Connection Issues

```python
# Test connection
from qdrant_client import QdrantClient
client = QdrantClient(
    url="https://xxx.qdrant.io",
    api_key="sk-..."
)
client.get_collections()  # Should return list of collections
```

### Collection Not Found

```python
# Create collection if missing
store.create_collection()
```

### Performance Degradation

- Check collection size: `store.get_collection_info()`
- If >1GB, consider archiving old vectors or upgrading tier
- Use filters to reduce search space

## Next Steps

1. [Implement Embedding Generation](./docs/embedding-generation.md)
2. [Content Ingestion](./docs/content-ingestion.md)
3. [Retrieval Agent](./docs/retrieval-agent.md)

## References

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [API Reference](https://qdrant.tech/api-reference/)
- [Python Client](https://github.com/qdrant/qdrant-client)
