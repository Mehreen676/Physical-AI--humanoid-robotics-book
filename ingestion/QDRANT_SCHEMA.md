# Qdrant Collection Schema

This document describes the vector collection schema used for storing book content embeddings.

## Collection Configuration

**Collection Name**: `data_collection` (configurable via `COLLECTION_NAME`)

**Vector Configuration**:
- **Size**: 768 dimensions (Gemini embedding-001 model)
- **Distance Metric**: Cosine similarity
- **Index Type**: HNSW (Hierarchical Navigable Small World) - default

## Vector Point Structure

Each point in the collection represents a chunk of book content.

### Point ID

**Type**: UUID (string)

**Generation**: Stable MD5-based UUID from `source_file::chunk_index`

**Example**: `"3f2504e0-4f89-11d3-9a0c-0305e82c3301"`

**Purpose**:
- Enables idempotent re-ingestion
- Prevents duplicate chunks
- Allows updating existing chunks

### Payload Schema

Each point contains the following payload fields:

#### `text` (string, required)

The actual text content of the chunk.

**Example**:
```json
{
  "text": "ROS 2 (Robot Operating System 2) is a flexible framework for writing robot software. It is a collection of tools, libraries, and conventions that aim to simplify the task of creating complex and robust robot behavior across a wide variety of robotic platforms."
}
```

#### `book_title` (string, required)

The title of the book.

**Example**: `"Physical AI & Humanoid Robotics Textbook"`

#### `chapter` (string, required)

The chapter name extracted from the directory structure.

**Extraction**: Directory name with number prefix removed and converted to title case.

**Example**:
- Directory: `02-ros2-foundations`
- Chapter: `"Ros2 Foundations"`

#### `section` (string, required)

The section name extracted from the filename.

**Extraction**: Filename (without extension) with number prefix removed and converted to title case.

**Example**:
- File: `module-1-ros2.md`
- Section: `"Module 1 Ros2"`

#### `source_file` (string, required)

Relative path to the original markdown file from the docs root.

**Example**: `"02-ros2-foundations/module-1-ros2.md"`

#### `chunk_index` (integer, required)

Zero-based index of this chunk within the source file.

**Example**: `2` (third chunk from the file)

#### `total_chunks` (integer, required)

Total number of chunks created from the source file.

**Example**: `12`

#### `token_count` (integer, required)

Number of tokens in this specific chunk.

**Example**: `387`

#### `start_token` (integer, optional)

Starting token position in the original document.

**Example**: `200`

#### `end_token` (integer, optional)

Ending token position in the original document.

**Example**: `600`

## Complete Example Point

```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "vector": [0.123, -0.456, 0.789, ...],  // 768 dimensions
  "payload": {
    "text": "ROS 2 (Robot Operating System 2) is a flexible framework for writing robot software. It is a collection of tools, libraries, and conventions that aim to simplify the task of creating complex and robust robot behavior across a wide variety of robotic platforms.",
    "book_title": "Physical AI & Humanoid Robotics Textbook",
    "chapter": "Ros2 Foundations",
    "section": "Module 1 Ros2",
    "source_file": "02-ros2-foundations/module-1-ros2.md",
    "chunk_index": 2,
    "total_chunks": 12,
    "token_count": 387,
    "start_token": 200,
    "end_token": 587
  }
}
```

## Similarity Search

### Query Vector

**Dimension**: 768 (must match collection dimension)

**Generation**: Same Gemini embedding model used for ingestion

### Filters

You can filter search results by metadata fields:

**Example 1: Search only in specific chapter**
```python
filter_dict = {"chapter": "Ros2 Foundations"}
```

**Example 2: Search only in specific source file**
```python
filter_dict = {"source_file": "02-ros2-foundations/module-1-ros2.md"}
```

**Example 3: Search only first chunks**
```python
filter_dict = {"chunk_index": 0}
```

### Similarity Score

**Metric**: Cosine similarity

**Range**: -1.0 to 1.0
- `1.0`: Identical vectors
- `0.0`: Orthogonal (unrelated)
- `-1.0`: Opposite vectors

**Typical Ranges**:
- `> 0.7`: Highly relevant
- `0.5 - 0.7`: Moderately relevant
- `0.3 - 0.5`: Potentially relevant
- `< 0.3`: Likely not relevant

### Search Parameters

**limit**: Maximum number of results (default: 5)

**score_threshold**: Minimum similarity score (default: 0.3)

**Example Search**:
```python
results = vector_store.search(
    query_vector=query_embedding,
    limit=5,
    score_threshold=0.5,
    filter_dict={"chapter": "Ros2 Foundations"}
)
```

## Collection Metadata

The collection itself has metadata:

- **vectors_count**: Total number of vectors indexed
- **points_count**: Total number of points stored
- **indexed_vectors_count**: Number of indexed vectors (for HNSW)
- **status**: Collection status (e.g., "green", "yellow", "red")

**Example**:
```json
{
  "name": "COSINE",
  "vectors_count": 156,
  "points_count": 156,
  "indexed_vectors_count": 156,
  "status": "GREEN"
}
```

## Indexing Strategy

**Index Type**: HNSW (Hierarchical Navigable Small World)

**Advantages**:
- Fast approximate nearest neighbor search
- Memory efficient
- Good balance between search speed and accuracy

**Configuration** (defaults):
- `m`: 16 (max connections per node)
- `ef_construct`: 100 (construction time trade-off)

## Storage Estimates

**Per Point**:
- Vector: 768 floats × 4 bytes = 3,072 bytes
- Payload: ~500-1000 bytes (varies by chunk size)
- Total: ~3.5-4 KB per point

**Example Collection** (18 documents, 156 chunks):
- Total storage: ~550-625 KB
- Well within Qdrant Cloud free tier (1 GB)

## Best Practices

### Querying

1. **Use Filters**: Filter by chapter/section for focused retrieval
2. **Set Thresholds**: Use `score_threshold` to filter low-quality results
3. **Adjust Limit**: Start with 5 results, increase if needed
4. **Cache Results**: Cache frequently accessed chunks

### Metadata

1. **Consistent Naming**: Use same field names across all points
2. **Normalize Text**: Lowercase chapter/section names for consistent filtering
3. **Add Timestamps**: Consider adding ingestion timestamp for versioning
4. **Preserve URLs**: Add GitHub Pages URL for click-through to source

### Maintenance

1. **Monitor Size**: Track points_count and vectors_count
2. **Re-index**: Recreate collection if schema changes
3. **Backup**: Export collection periodically
4. **Version**: Use collection naming with versions (e.g., `book_v1`, `book_v2`)

## Schema Evolution

To update the schema:

1. **Create New Collection**: `book_v2` with new schema
2. **Re-ingest Content**: Run ingestion pipeline with updated code
3. **Test New Collection**: Validate search quality
4. **Switch Production**: Update `COLLECTION_NAME` to `book_v2`
5. **Delete Old Collection**: Remove `book_v1` after validation

## Troubleshooting

### Issue: "Vector dimension mismatch"

**Cause**: Embedding model changed or incorrect dimension configured

**Solution**: Ensure all vectors are 768 dimensions (Gemini embedding-001)

### Issue: "Point ID collision"

**Cause**: Non-deterministic ID generation or duplicate chunks

**Solution**: Use stable UUID generation from `source_file::chunk_index`

### Issue: "Low search quality"

**Cause**: Irrelevant chunks retrieved

**Solution**:
- Increase `score_threshold` to filter low-quality results
- Use metadata filters to narrow search scope
- Review chunking strategy (size/overlap)

### Issue: "Slow queries"

**Cause**: Large collection or inefficient indexing

**Solution**:
- Ensure HNSW index is built (check `indexed_vectors_count`)
- Increase `ef_construct` for better index quality
- Use filters to reduce search space

---

**Last Updated**: 2026-01-03

**Schema Version**: 1.0.0
