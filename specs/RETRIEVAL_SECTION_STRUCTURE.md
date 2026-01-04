# Semantic Retrieval Layer - Section Structure

## Module Organization

This document outlines the detailed section structure for implementing the semantic retrieval module, organized by functional responsibility.

---

## Section 1: Input Handling (Query / Optional Selected Text)

### 1.1 Input Validation

**File**: `retrieval/input_handler.py`

**Purpose**: Validate and sanitize user inputs before processing

**Components**:

```python
class InputValidator:
    """Validates retrieval inputs."""

    @staticmethod
    def validate_query(query: str) -> str:
        """
        Validate and sanitize query text.

        Checks:
        - Query is not None or empty
        - Query length is reasonable (< 1000 chars)
        - Trim whitespace

        Args:
            query: User's question

        Returns:
            Sanitized query string

        Raises:
            ValidationError: If query is invalid
        """

    @staticmethod
    def validate_selected_text(
        selected_text: Optional[str],
        retrieval_mode: str
    ) -> Optional[str]:
        """
        Validate selected text for selected-text mode.

        Checks:
        - If mode="selected_text", selected_text must be provided
        - Selected text length is reasonable (< 2000 chars)
        - Trim whitespace

        Args:
            selected_text: Text selected by user
            retrieval_mode: "normal" or "selected_text"

        Returns:
            Sanitized selected text or None

        Raises:
            ValidationError: If required but missing
        """

    @staticmethod
    def detect_retrieval_mode(
        query: str,
        selected_text: Optional[str]
    ) -> str:
        """
        Detect retrieval mode based on inputs.

        Logic:
        - If selected_text provided → "selected_text"
        - Otherwise → "normal"

        Args:
            query: User's question
            selected_text: Optional selected text

        Returns:
            "normal" or "selected_text"
        """
```

### 1.2 Input Logging

**Purpose**: Log incoming requests for debugging and auditing

**Implementation**:

```python
def log_input_received(
    query: str,
    retrieval_mode: str,
    selected_text: Optional[str]
) -> None:
    """
    Log incoming retrieval request.

    Logs:
    - Timestamp
    - Query length (not content, for privacy)
    - Retrieval mode
    - Whether selected text provided

    Example log:
    {
        "timestamp": "2026-01-03T12:00:00Z",
        "level": "INFO",
        "event": "retrieval_request",
        "query_length": 15,
        "retrieval_mode": "normal",
        "has_selected_text": false
    }
    """
```

### 1.3 Input Schema

**File**: `retrieval/schemas.py`

**Purpose**: Define Pydantic models for type safety

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal

class RetrievalRequest(BaseModel):
    """Input schema for retrieval requests."""

    query: str = Field(..., min_length=1, max_length=1000)
    retrieval_mode: Literal["normal", "selected_text"] = "normal"
    selected_text: Optional[str] = Field(None, max_length=2000)
    top_k: Optional[int] = Field(None, ge=1, le=10)
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)

    @validator('selected_text')
    def validate_selected_text_for_mode(cls, v, values):
        """Ensure selected_text provided if mode='selected_text'."""
        if values.get('retrieval_mode') == 'selected_text' and not v:
            raise ValueError("selected_text required for selected_text mode")
        return v
```

---

## Section 2: Embedding Generation (Gemini Free-Tier)

### 2.1 Embedding Service Interface

**File**: `retrieval/embeddings.py`

**Purpose**: Abstract embedding service for swappable providers

```python
from abc import ABC, abstractmethod
from typing import List

class EmbeddingService(ABC):
    """Abstract base class for embedding services."""

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for query text.

        Args:
            text: Query or selected text to embed

        Returns:
            768-dimensional embedding vector

        Raises:
            EmbeddingError: If embedding generation fails
        """

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get embedding dimension.

        Returns:
            768 for Gemini embeddings-001
        """
```

### 2.2 Gemini Embeddings Implementation

**Purpose**: Integrate Google Gemini embeddings-001 API

```python
import google.generativeai as genai
from typing import List
import time

class GeminiEmbeddings(EmbeddingService):
    """Gemini embeddings-001 service."""

    def __init__(self, api_key: str):
        """
        Initialize Gemini embeddings service.

        Args:
            api_key: Google Gemini API key

        Free-tier limits:
        - 15 requests/min
        - 1,500 requests/day
        """
        genai.configure(api_key=api_key)
        self.model = "models/embedding-001"
        self.dimension = 768
        self._last_request_time = 0
        self._min_request_interval = 4.0  # 15/min = 1 every 4s

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for query text.

        Rate limiting:
        - Enforces 4s minimum between requests
        - Prevents quota exhaustion

        Args:
            text: Query text

        Returns:
            768-dimensional embedding vector
        """
        # Rate limiting
        self._enforce_rate_limit()

        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_query"
            )
            embedding = result['embedding']

            # Validation
            if len(embedding) != self.dimension:
                raise EmbeddingError(f"Expected {self.dimension} dims, got {len(embedding)}")

            return embedding

        except Exception as e:
            logger.error(f"Gemini embedding failed: {e}")
            raise EmbeddingError(f"Failed to generate embedding: {e}")

    def _enforce_rate_limit(self):
        """Enforce rate limit with sleep if needed."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def get_embedding_dimension(self) -> int:
        return self.dimension
```

### 2.3 Mock Embeddings (Fallback)

**Purpose**: Provide deterministic fallback when Gemini quota exceeded

```python
import hashlib
import numpy as np
from typing import List

class MockEmbeddings(EmbeddingService):
    """Mock embeddings using deterministic hashing."""

    def __init__(self):
        """Initialize mock embeddings service."""
        self.dimension = 768
        logger.warning("Using MockEmbeddings (Gemini quota exhausted)")

    def embed_query(self, text: str) -> List[float]:
        """
        Generate deterministic mock embedding.

        Uses MD5 hash of text as seed for reproducible vectors.

        Args:
            text: Query text

        Returns:
            768-dimensional normalized vector
        """
        # Create seed from text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)

        # Generate reproducible random vector
        np.random.seed(seed)
        embedding = np.random.randn(self.dimension)

        # Normalize to unit length
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.tolist()

    def get_embedding_dimension(self) -> int:
        return self.dimension
```

### 2.4 Embedding Service Factory

**Purpose**: Choose embedding provider based on configuration

```python
import os

def get_embedding_service() -> EmbeddingService:
    """
    Factory function to get embedding service.

    Returns Gemini or Mock based on environment variable.

    Returns:
        GeminiEmbeddings or MockEmbeddings

    Environment Variables:
        USE_MOCK_EMBEDDINGS: "true" to use mock, "false" for Gemini
        GEMINI_API_KEY: Required if using Gemini
    """
    use_mock = os.getenv("USE_MOCK_EMBEDDINGS", "false").lower() == "true"

    if use_mock:
        logger.info("Using MockEmbeddings (configured)")
        return MockEmbeddings()
    else:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ConfigurationError("GEMINI_API_KEY required for Gemini embeddings")
        logger.info("Using GeminiEmbeddings")
        return GeminiEmbeddings(api_key=api_key)
```

### 2.5 Embedding Validation

**Purpose**: Ensure embedding quality and consistency

```python
def validate_embedding(embedding: List[float]) -> bool:
    """
    Validate embedding vector.

    Checks:
    - Dimension is 768
    - All values are finite (no NaN, Inf)
    - Vector is normalized (L2 norm ≈ 1.0)

    Args:
        embedding: Embedding vector

    Returns:
        True if valid

    Raises:
        ValidationError: If invalid
    """
    # Check dimension
    if len(embedding) != 768:
        raise ValidationError(f"Expected 768 dims, got {len(embedding)}")

    # Check for NaN/Inf
    if not all(np.isfinite(embedding)):
        raise ValidationError("Embedding contains NaN or Inf")

    # Check normalization (allow 5% tolerance)
    norm = np.linalg.norm(embedding)
    if not (0.95 <= norm <= 1.05):
        logger.warning(f"Embedding not normalized: L2 norm = {norm}")

    return True
```

---

## Section 3: Qdrant Semantic Search (Top-k, Cosine Similarity)

### 3.1 Qdrant Client Wrapper

**File**: `retrieval/qdrant_client.py`

**Purpose**: Wrap Qdrant API for semantic search

```python
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint
from typing import List
import os

class QdrantRetriever:
    """Wrapper for Qdrant semantic search."""

    def __init__(
        self,
        url: str,
        api_key: str,
        collection_name: str
    ):
        """
        Initialize Qdrant client.

        Args:
            url: Qdrant Cloud endpoint
            api_key: Qdrant API key
            collection_name: Vector collection name

        Raises:
            ConnectionError: If cannot connect to Qdrant
        """
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection_name = collection_name

        # Validate connection
        self._validate_connection()

    def _validate_connection(self):
        """Validate Qdrant connection and collection exists."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                raise CollectionNotFoundError(
                    f"Collection '{self.collection_name}' not found. "
                    f"Available: {collection_names}"
                )

            logger.info(f"Connected to Qdrant collection: {self.collection_name}")

        except Exception as e:
            raise ConnectionError(f"Failed to connect to Qdrant: {e}")

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.7
    ) -> List[ScoredPoint]:
        """
        Search Qdrant for similar vectors.

        Search parameters:
        - Distance metric: Cosine similarity
        - Returns: Top-k results above score_threshold
        - Sorted: By score descending

        Args:
            query_vector: 768-dimensional query embedding
            top_k: Number of results to return
            score_threshold: Minimum similarity score

        Returns:
            List of ScoredPoint objects

        Raises:
            SearchError: If search fails
        """
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False  # Don't return stored vectors
            )

            logger.info(
                f"Qdrant search: found {len(results)} results "
                f"(k={top_k}, threshold={score_threshold})"
            )

            return results

        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            raise SearchError(f"Search failed: {e}")
```

### 3.2 Retry Logic with Exponential Backoff

**Purpose**: Handle transient network failures

```python
import time
from typing import Callable, TypeVar, List

T = TypeVar('T')

def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> T:
    """
    Retry function with exponential backoff.

    Retry delays:
    - 1st retry: 1s
    - 2nd retry: 2s
    - 3rd retry: 4s

    Args:
        func: Function to retry
        max_retries: Maximum retry attempts
        initial_delay: Initial delay in seconds

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()

        except Exception as e:
            last_exception = e

            if attempt < max_retries:
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error(f"All {max_retries + 1} attempts failed")

    raise last_exception
```

### 3.3 Search Parameter Configuration

**Purpose**: Configure search parameters per mode

```python
from dataclasses import dataclass

@dataclass
class SearchConfig:
    """Search configuration for different modes."""
    top_k: int
    score_threshold: float

# Normal mode: broader search
NORMAL_SEARCH_CONFIG = SearchConfig(
    top_k=5,
    score_threshold=0.70
)

# Selected-text mode: narrower, higher precision
SELECTED_TEXT_SEARCH_CONFIG = SearchConfig(
    top_k=3,
    score_threshold=0.85
)

def get_search_config(retrieval_mode: str) -> SearchConfig:
    """
    Get search configuration for mode.

    Args:
        retrieval_mode: "normal" or "selected_text"

    Returns:
        SearchConfig with appropriate parameters
    """
    if retrieval_mode == "selected_text":
        return SELECTED_TEXT_SEARCH_CONFIG
    else:
        return NORMAL_SEARCH_CONFIG
```

---

## Section 4: Result Formatting with Metadata

### 4.1 Result Schema

**File**: `retrieval/schemas.py`

**Purpose**: Define output schema for type safety

```python
from pydantic import BaseModel
from typing import Dict, List

class ChunkMetadata(BaseModel):
    """Metadata for retrieved chunk."""
    chapter: str
    section: str
    source_file: str
    chunk_index: int
    total_chunks: int
    token_count: int

class RetrievedChunk(BaseModel):
    """Single retrieved chunk with metadata and score."""
    text: str
    metadata: ChunkMetadata
    score: float

class RetrievalResponse(BaseModel):
    """Response schema for retrieval requests."""
    chunks: List[RetrievedChunk]
    metadata: Dict[str, any] = {
        "num_results": int,
        "retrieval_mode": str,
        "latency_ms": int
    }
```

### 4.2 Result Formatter

**File**: `retrieval/formatter.py`

**Purpose**: Convert Qdrant results to standard schema

```python
from qdrant_client.models import ScoredPoint
from typing import List, Dict

class ResultFormatter:
    """Formats Qdrant search results."""

    @staticmethod
    def format_results(
        scored_points: List[ScoredPoint]
    ) -> List[Dict]:
        """
        Format Qdrant ScoredPoint objects to standard schema.

        Args:
            scored_points: Raw Qdrant search results

        Returns:
            List of formatted chunks with metadata

        Quality checks:
        - Validate all required metadata fields present
        - Ensure scores in descending order
        - Verify text not empty
        - Check chunk_index < total_chunks
        """
        formatted_chunks = []

        for point in scored_points:
            try:
                chunk = ResultFormatter._format_single_chunk(point)
                formatted_chunks.append(chunk)
            except Exception as e:
                logger.warning(f"Skipping chunk due to formatting error: {e}")
                continue

        # Validate ordering
        ResultFormatter._validate_ordering(formatted_chunks)

        return formatted_chunks

    @staticmethod
    def _format_single_chunk(point: ScoredPoint) -> Dict:
        """Format single Qdrant point."""
        payload = point.payload

        # Extract and validate metadata
        metadata = payload.get("metadata", {})

        required_fields = [
            "chapter", "section", "source_file",
            "chunk_index", "total_chunks", "token_count"
        ]

        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required field: {field}")

        # Validate text
        text = payload.get("text", "")
        if not text or not text.strip():
            raise ValueError("Empty text content")

        # Validate chunk index
        if metadata["chunk_index"] >= metadata["total_chunks"]:
            raise ValueError(
                f"Invalid chunk_index: {metadata['chunk_index']} >= "
                f"{metadata['total_chunks']}"
            )

        return {
            "text": text.strip(),
            "metadata": {
                "chapter": metadata["chapter"],
                "section": metadata["section"],
                "source_file": metadata["source_file"],
                "chunk_index": metadata["chunk_index"],
                "total_chunks": metadata["total_chunks"],
                "token_count": metadata["token_count"]
            },
            "score": float(point.score)
        }

    @staticmethod
    def _validate_ordering(chunks: List[Dict]):
        """Validate chunks are sorted by score descending."""
        scores = [chunk["score"] for chunk in chunks]

        if scores != sorted(scores, reverse=True):
            logger.warning("Results not in descending score order")
            # Sort in place
            chunks.sort(key=lambda x: x["score"], reverse=True)
```

### 4.3 Metadata Integrity Validation

**Purpose**: Ensure all metadata fields are valid

```python
def validate_metadata_integrity(chunks: List[Dict]) -> bool:
    """
    Validate metadata integrity across all chunks.

    Checks:
    - All required fields present
    - No duplicate chunks (by text hash)
    - chunk_index < total_chunks for all
    - All token_counts > 0

    Args:
        chunks: List of formatted chunks

    Returns:
        True if valid

    Raises:
        ValidationError: If integrity check fails
    """
    seen_hashes = set()

    for chunk in chunks:
        metadata = chunk["metadata"]

        # Check for duplicates
        text_hash = hashlib.md5(chunk["text"].encode()).hexdigest()
        if text_hash in seen_hashes:
            raise ValidationError("Duplicate chunk detected")
        seen_hashes.add(text_hash)

        # Validate chunk index
        if metadata["chunk_index"] >= metadata["total_chunks"]:
            raise ValidationError(
                f"Invalid chunk_index: {metadata['chunk_index']}"
            )

        # Validate token count
        if metadata["token_count"] <= 0:
            raise ValidationError(
                f"Invalid token_count: {metadata['token_count']}"
            )

    return True
```

---

## Section 5: Optional Selected-Text Context Handling

### 5.1 Mode Detection Logic

**Purpose**: Determine retrieval strategy based on inputs

```python
def determine_retrieval_strategy(
    query: str,
    selected_text: Optional[str],
    retrieval_mode: str
) -> Dict[str, any]:
    """
    Determine retrieval strategy based on inputs.

    Logic:
    - If retrieval_mode="selected_text" and selected_text provided:
        → Use selected-text strategy
    - Otherwise:
        → Use normal strategy

    Args:
        query: User's question
        selected_text: Optional selected text
        retrieval_mode: Explicit mode from user

    Returns:
        {
            "strategy": "normal" or "selected_text",
            "text_to_embed": str (query or selected_text),
            "search_config": SearchConfig
        }
    """
    if retrieval_mode == "selected_text":
        if not selected_text:
            raise ValidationError(
                "selected_text required for selected_text mode"
            )

        return {
            "strategy": "selected_text",
            "text_to_embed": selected_text,  # Key difference!
            "search_config": SELECTED_TEXT_SEARCH_CONFIG
        }
    else:
        return {
            "strategy": "normal",
            "text_to_embed": query,
            "search_config": NORMAL_SEARCH_CONFIG
        }
```

### 5.2 Selected-Text Retrieval Flow

**Purpose**: Implement constrained retrieval for selected text

```python
def retrieve_with_selected_text(
    query: str,
    selected_text: str,
    embedding_service: EmbeddingService,
    qdrant_client: QdrantRetriever
) -> List[Dict]:
    """
    Retrieve chunks constrained to selected text context.

    Process:
    1. Embed selected_text (NOT query!)
    2. Search Qdrant with stricter parameters (k=3, threshold=0.85)
    3. Return highly similar chunks only

    This constrains the retrieval context to passage user selected.

    Args:
        query: User's question (not used for embedding!)
        selected_text: Text selected by user
        embedding_service: Embedding service
        qdrant_client: Qdrant client

    Returns:
        List of chunks highly similar to selected text
    """
    logger.info(
        f"Selected-text retrieval: "
        f"query='{query[:50]}...', "
        f"selection_length={len(selected_text)}"
    )

    # IMPORTANT: Embed selected_text, not query!
    selection_embedding = embedding_service.embed_query(selected_text)

    # Search with stricter parameters
    config = SELECTED_TEXT_SEARCH_CONFIG
    results = qdrant_client.search(
        query_vector=selection_embedding,
        top_k=config.top_k,  # 3 (fewer results)
        score_threshold=config.score_threshold  # 0.85 (higher threshold)
    )

    # Format and return
    formatted_chunks = ResultFormatter.format_results(results)

    logger.info(
        f"Selected-text retrieval returned {len(formatted_chunks)} chunks "
        f"(threshold={config.score_threshold})"
    )

    return formatted_chunks
```

### 5.3 Fallback Handling

**Purpose**: Handle cases where selected-text retrieval returns no results

```python
def retrieve_with_fallback(
    query: str,
    selected_text: Optional[str],
    retrieval_mode: str,
    embedding_service: EmbeddingService,
    qdrant_client: QdrantRetriever
) -> List[Dict]:
    """
    Retrieve with fallback logic.

    Strategy:
    1. Try selected-text retrieval if mode="selected_text"
    2. If no results (empty list), fallback to normal retrieval
    3. Log fallback for monitoring

    Args:
        query: User's question
        selected_text: Optional selected text
        retrieval_mode: Retrieval mode
        embedding_service: Embedding service
        qdrant_client: Qdrant client

    Returns:
        Retrieved chunks (never empty if fallback succeeds)
    """
    if retrieval_mode == "selected_text":
        chunks = retrieve_with_selected_text(
            query, selected_text, embedding_service, qdrant_client
        )

        if not chunks:
            logger.warning(
                "Selected-text retrieval returned no results. "
                "Falling back to normal retrieval."
            )
            chunks = retrieve_normal(
                query, embedding_service, qdrant_client
            )

        return chunks
    else:
        return retrieve_normal(
            query, embedding_service, qdrant_client
        )
```

---

## Section 6: Logging and Error Handling

### 6.1 Structured Logging Setup

**File**: `retrieval/logger.py`

**Purpose**: Configure structured JSON logging

```python
import logging
import json
from datetime import datetime
from typing import Dict, Any

class StructuredLogger:
    """Structured JSON logger for retrieval events."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)

    def log_event(
        self,
        event: str,
        level: str = "INFO",
        **kwargs
    ):
        """
        Log structured event.

        Args:
            event: Event name
            level: Log level (INFO, WARNING, ERROR)
            **kwargs: Additional fields
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "event": event,
            **kwargs
        }

        if level == "INFO":
            self.logger.info(json.dumps(log_entry))
        elif level == "WARNING":
            self.logger.warning(json.dumps(log_entry))
        elif level == "ERROR":
            self.logger.error(json.dumps(log_entry))

class JsonFormatter(logging.Formatter):
    """Format logs as JSON."""

    def format(self, record):
        return record.getMessage()
```

### 6.2 Retrieval Event Logging

**Purpose**: Log all retrieval phases

```python
def log_retrieval_phases(
    query: str,
    retrieval_mode: str,
    embedding_latency_ms: int,
    search_latency_ms: int,
    num_results: int,
    total_latency_ms: int
):
    """
    Log complete retrieval pipeline.

    Logs:
    - Query received
    - Embedding generated
    - Search completed
    - Results formatted
    - Total latency

    Args:
        query: User's question
        retrieval_mode: Retrieval mode
        embedding_latency_ms: Embedding generation time
        search_latency_ms: Qdrant search time
        num_results: Number of results returned
        total_latency_ms: Total end-to-end latency
    """
    logger.log_event(
        event="query_received",
        query_length=len(query),
        retrieval_mode=retrieval_mode
    )

    logger.log_event(
        event="embedding_generated",
        latency_ms=embedding_latency_ms
    )

    logger.log_event(
        event="search_completed",
        latency_ms=search_latency_ms,
        num_results=num_results
    )

    logger.log_event(
        event="retrieval_completed",
        total_latency_ms=total_latency_ms,
        num_results=num_results
    )
```

### 6.3 Error Handling Hierarchy

**File**: `retrieval/errors.py`

**Purpose**: Define custom exceptions

```python
class RetrievalError(Exception):
    """Base exception for retrieval errors."""

class ValidationError(RetrievalError):
    """Input validation error."""

class EmbeddingError(RetrievalError):
    """Embedding generation error."""

class SearchError(RetrievalError):
    """Qdrant search error."""

class ConnectionError(RetrievalError):
    """Qdrant connection error."""

class CollectionNotFoundError(RetrievalError):
    """Qdrant collection not found."""

class ConfigurationError(RetrievalError):
    """Configuration error (missing env vars)."""
```

### 6.4 Error Logging with Context

**Purpose**: Log errors with full context for debugging

```python
def log_error_with_context(
    error: Exception,
    phase: str,
    context: Dict[str, Any]
):
    """
    Log error with full context.

    Args:
        error: Exception that occurred
        phase: Retrieval phase where error occurred
        context: Additional context (query, mode, etc.)
    """
    logger.log_event(
        event="error_occurred",
        level="ERROR",
        phase=phase,
        error_type=type(error).__name__,
        error_message=str(error),
        **context
    )
```

---

## Integration Example

**File**: `retrieval/retriever.py`

**Purpose**: Main orchestrator integrating all sections

```python
class SemanticRetriever:
    """Main semantic retrieval orchestrator."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        qdrant_client: QdrantRetriever
    ):
        """Initialize retriever with services."""
        self.embedding_service = embedding_service
        self.qdrant_client = qdrant_client
        self.logger = StructuredLogger("semantic_retriever")

    def retrieve(
        self,
        query: str,
        retrieval_mode: str = "normal",
        selected_text: Optional[str] = None,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Main retrieval method integrating all sections.

        Sections used:
        1. Input validation (Section 1)
        2. Embedding generation (Section 2)
        3. Qdrant search (Section 3)
        4. Result formatting (Section 4)
        5. Selected-text handling (Section 5)
        6. Logging (Section 6)

        Args:
            query: User's question
            retrieval_mode: "normal" or "selected_text"
            selected_text: Optional selected text
            top_k: Override default top_k
            score_threshold: Override default threshold

        Returns:
            List of retrieved chunks with metadata
        """
        start_time = time.time()

        try:
            # Section 1: Input validation
            query = InputValidator.validate_query(query)
            selected_text = InputValidator.validate_selected_text(
                selected_text, retrieval_mode
            )

            # Section 6: Log input
            self.logger.log_event(
                event="query_received",
                query_length=len(query),
                retrieval_mode=retrieval_mode
            )

            # Section 5: Determine strategy
            strategy = determine_retrieval_strategy(
                query, selected_text, retrieval_mode
            )

            # Section 2: Generate embedding
            embedding_start = time.time()
            embedding = self.embedding_service.embed_query(
                strategy["text_to_embed"]
            )
            embedding_latency = int((time.time() - embedding_start) * 1000)

            # Section 6: Log embedding
            self.logger.log_event(
                event="embedding_generated",
                latency_ms=embedding_latency
            )

            # Section 3: Search Qdrant
            search_start = time.time()
            config = strategy["search_config"]
            results = self.qdrant_client.search(
                query_vector=embedding,
                top_k=top_k or config.top_k,
                score_threshold=score_threshold or config.score_threshold
            )
            search_latency = int((time.time() - search_start) * 1000)

            # Section 4: Format results
            formatted_chunks = ResultFormatter.format_results(results)

            # Section 4: Validate metadata
            validate_metadata_integrity(formatted_chunks)

            # Section 6: Log completion
            total_latency = int((time.time() - start_time) * 1000)
            self.logger.log_event(
                event="retrieval_completed",
                total_latency_ms=total_latency,
                num_results=len(formatted_chunks)
            )

            return formatted_chunks

        except Exception as e:
            # Section 6: Log error
            log_error_with_context(
                error=e,
                phase="retrieval",
                context={
                    "query_length": len(query),
                    "retrieval_mode": retrieval_mode
                }
            )
            raise
```

---

**Last Updated**: 2026-01-03

**Status**: Section structure complete

**Next**: Use this structure as implementation guide for all 6 sections
