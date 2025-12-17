# Developer Guide: RAG Chatbot Backend

This guide explains how to extend, customize, and maintain the RAG Chatbot system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Setting Up Development](#setting-up-development)
4. [Core Components](#core-components)
5. [Adding Features](#adding-features)
6. [Customization Guide](#customization-guide)
7. [Testing & Debugging](#testing--debugging)
8. [Performance Optimization](#performance-optimization)
9. [Deployment](#deployment)

---

## Architecture Overview

### System Stack

```
┌─────────────────────────────────────────┐
│     Docusaurus Textbook (Frontend)      │
│  React Components + Chat Widget         │
└────────────────────┬────────────────────┘
                     │ HTTPS REST API
                     ▼
┌─────────────────────────────────────────┐
│    FastAPI Backend (RAG Service)        │
│  - Request handling & validation        │
│  - RAG pipeline orchestration           │
│  - Session & message management         │
└────────────────────┬────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌────────┐ ┌────────┐ ┌──────────┐
    │ Qdrant │ │ Neon   │ │ OpenAI   │
    │ Cloud  │ │Postgres│ │   API    │
    │Vectors │ │Metadata│ │    LLM   │
    └────────┘ └────────┘ └──────────┘
```

### Data Flow

1. **User Query** → Frontend sends to `/query`
2. **Validation** → Input validation & sanitization
3. **Embedding** → Query embedded via OpenAI
4. **Retrieval** → Semantic search in Qdrant
5. **Re-ranking** → Results ranked by relevance
6. **Generation** → Prompt + context → LLM
7. **Storage** → Session saved to Neon
8. **Response** → Answer returned with sources

---

## Project Structure

```
rag-backend/
├── src/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration & env vars
│   ├── security.py             # Auth, validation, sanitization
│   ├── database.py             # SQLAlchemy ORM models
│   ├── vector_store.py         # Qdrant integration
│   ├── embeddings.py           # OpenAI embeddings
│   ├── chunking.py             # Content chunking logic
│   ├── ingest_service.py       # Content ingestion
│   ├── retrieval_service.py    # Semantic search
│   ├── generation_service.py   # LLM response generation
│   ├── validation.py           # Input/output validation
│   └── api_keys.py             # API key management
├── tests/
│   ├── test_*.py              # Unit tests (80+ tests)
│   ├── test_performance.py    # Performance benchmarks
│   └── test_security_hardening.py  # Security tests
├── Dockerfile                  # Container definition
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── USER_GUIDE.md              # End-user documentation
├── DEVELOPER_GUIDE.md         # This file
├── DEPLOYMENT_GUIDE.md        # Deployment instructions
└── README.md                  # Project overview
```

---

## Setting Up Development

### Prerequisites

- Python 3.13+
- PostgreSQL 15+ (or Docker)
- Git
- Virtual environment tool (venv)

### Initial Setup

1. **Clone repository**
   ```bash
   git clone <repo-url>
   cd rag-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8 pylint  # Dev tools
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run tests**
   ```bash
   pytest tests/ -v
   ```

6. **Start development server**
   ```bash
   uvicorn src.main:app --reload
   ```

   Access at: http://localhost:8000/docs

---

## Core Components

### 1. Main Application (`main.py`)

Entry point for FastAPI application.

```python
from fastapi import FastAPI
from src.config import get_settings

app = FastAPI(title="RAG Chatbot API")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/query")
async def query(request: QueryRequest):
    # Full RAG pipeline
    return response
```

**Key endpoints:**
- `GET /health` - Health check
- `POST /query` - Full-book query
- `POST /ingest` - Add content
- `GET /sessions/{id}` - Get chat history

### 2. Configuration (`config.py`)

Centralized environment management.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    qdrant_url: str
    database_url: str
    # ... more settings
```

**Key patterns:**
- Pydantic validation
- Default fallbacks
- Per-environment overrides

### 3. Vector Store (`vector_store.py`)

Qdrant Cloud integration for semantic search.

```python
class QdrantVectorStore:
    def query_vectors(self, query_vector, top_k=5):
        # Semantic search
        return results
```

**Key methods:**
- `create_collection()` - Create vector collection
- `store_vector()` - Store embedding + metadata
- `query_vectors()` - Similarity search

### 4. Embeddings (`embeddings.py`)

OpenAI embedding generation.

```python
class EmbeddingGenerator:
    def embed_text(self, text: str) -> List[float]:
        # Generate 1536-dim embedding
        return embedding_vector
```

**Features:**
- Batch processing (up to 2048 texts)
- Retry logic for rate limiting
- Cost tracking

### 5. Retrieval Service (`retrieval_service.py`)

Orchestrates semantic search.

```python
class RetrievalService:
    def retrieve_context(self, query: str, top_k: int = 5):
        # Embed query
        # Search vectors
        # Rank results
        return contexts
```

### 6. Generation Service (`generation_service.py`)

LLM response generation with fallback.

```python
class GenerationService:
    def generate_response(self, query: str, context: str):
        # Build prompt
        # Call GPT-4o
        # Fallback to GPT-3.5-turbo if needed
        return response
```

---

## Adding Features

### Example: Add New Chat Mode

Let's add "Summary Mode" to generate summaries instead of Q&A.

**Step 1: Update Schema (`validation.py`)**

```python
class QueryRequest(BaseModel):
    query: str
    mode: Literal["full_book", "selected_text", "summary"]  # Add summary
```

**Step 2: Update Generation Service (`generation_service.py`)**

```python
def generate_response(self, query: str, context: str, mode: str):
    if mode == "summary":
        prompt = f"Summarize this in 3 bullet points: {context}"
    else:
        prompt = f"Answer: {query}\nContext: {context}"

    return await self.llm.generate(prompt)
```

**Step 3: Update Main Endpoint (`main.py`)**

```python
@app.post("/query")
async def query(request: QueryRequest):
    if request.mode == "summary":
        return await generation_service.generate_summary(request)
    else:
        return await rag_pipeline(request)
```

**Step 4: Add Tests (`tests/test_summary.py`)**

```python
def test_summary_mode():
    response = client.post("/query", {
        "query": "main points",
        "mode": "summary"
    })
    assert "bullet" in response["answer"].lower()
```

---

## Customization Guide

### 1. Change LLM Model

Update `config.py`:
```python
openai_llm_model: str = "gpt-4-turbo"  # Changed from gpt-4o
```

### 2. Customize Prompts

Edit `generation_service.py`:
```python
SYSTEM_PROMPT = """
You are an expert tutor. Answer questions about the textbook
in a clear, structured way with examples.
"""

def generate_response(self, query, context):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Q: {query}\nContext: {context}"}
    ]
    return self.llm.create_chat_completion(messages)
```

### 3. Add Custom Validation

Create `validators/custom.py`:
```python
def validate_technical_query(query: str) -> bool:
    keywords = ["algorithm", "API", "protocol", ...]
    return any(kw in query.lower() for kw in keywords)
```

Use in endpoints:
```python
@app.post("/query")
async def query(request: QueryRequest):
    if not validate_technical_query(request.query):
        raise HTTPException(400, "Please ask technical questions")
```

### 4. Change Retrieval Strategy

Modify `retrieval_service.py`:
```python
def retrieve_context(self, query: str, top_k: int = 5):
    # Current: vector similarity
    contexts = self.vector_store.query_vectors(embedding, top_k)

    # Custom: Add BM25 hybrid search
    bm25_results = self.bm25_index.search(query, top_k)

    # Combine and re-rank
    combined = self.rerank(contexts + bm25_results)
    return combined[:top_k]
```

---

## Testing & Debugging

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_security_hardening.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Performance tests only
pytest tests/test_performance.py -v
```

### Debugging

**Enable debug logging:**

Edit `config.py`:
```python
log_level: str = "DEBUG"  # Changed from INFO
```

**Add breakpoints:**

```python
import pdb; pdb.set_trace()  # Stops execution
```

**Check request/response:**

```python
@app.post("/query")
async def query(request: QueryRequest):
    print(f"Request: {request}")  # Log input
    response = await rag_pipeline(request)
    print(f"Response: {response}")  # Log output
    return response
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Slow responses | Check OpenAI API latency, add caching |
| High memory usage | Reduce batch sizes, implement streaming |
| DB connection errors | Verify DATABASE_URL, check pool size |
| Low accuracy | Improve prompts, add post-processing |

---

## Performance Optimization

### 1. Caching

Add Redis caching (optional):

```python
from redis import Redis

cache = Redis(host='localhost', port=6379)

async def get_cached_response(query: str):
    cached = cache.get(query)
    if cached:
        return json.loads(cached)

    response = await rag_pipeline(query)
    cache.set(query, json.dumps(response), ex=86400)  # 24h TTL
    return response
```

### 2. Batch Processing

Process multiple queries efficiently:

```python
async def batch_query(queries: List[str]):
    # Embed all at once
    embeddings = self.embedding_gen.embed_texts(queries)

    # Search all vectors
    results = [
        self.vector_store.query_vectors(emb)
        for emb in embeddings
    ]

    # Generate all responses
    responses = await asyncio.gather(
        *[self.generation_service.generate(q, r)
          for q, r in zip(queries, results)]
    )
    return responses
```

### 3. Query Optimization

Optimize database queries:

```python
# Before: N+1 query problem
sessions = db.query(ChatSession).all()
for session in sessions:
    messages = db.query(Message).filter_by(session_id=session.id).all()

# After: Join query
sessions = db.query(ChatSession).options(
    joinedload(ChatSession.messages)
).all()
```

---

## Deployment

### Deploying Changes

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and test**
   ```bash
   pytest tests/ -v
   ```

3. **Commit and push**
   ```bash
   git add .
   git commit -m "Add feature: my-feature"
   git push origin feature/my-feature
   ```

4. **Create pull request**
   - GitHub Actions runs tests
   - Deploy to staging if tests pass
   - Merge to main to deploy to production

### Environment-Specific Configuration

Different settings per environment:

```python
if settings.environment == "production":
    log_level = "WARNING"
    debug = False
    cache_ttl = 3600
elif settings.environment == "staging":
    log_level = "INFO"
    debug = False
    cache_ttl = 600
else:  # development
    log_level = "DEBUG"
    debug = True
    cache_ttl = 60
```

---

## Code Standards

### Style Guide

Follow PEP 8:
```bash
black src/  # Auto-format
flake8 src/ # Lint
pylint src/ # Analysis
```

### Docstrings

All functions should have docstrings:

```python
async def query(request: QueryRequest) -> QueryResponse:
    """
    Process user query through RAG pipeline.

    Args:
        request: User query with optional selected text

    Returns:
        QueryResponse with answer and sources

    Raises:
        HTTPException: If query validation fails
    """
```

### Type Hints

Always use type hints:

```python
def retrieve_context(
    query: str,
    top_k: int = 5,
    threshold: float = 0.5
) -> List[RetrievalResult]:
    """Retrieve relevant contexts from vector store."""
```

---

## Contributing

### Before Submitting PR

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Code formatted: `black src/`
- [ ] No lint errors: `flake8 src/`
- [ ] Docstrings added
- [ ] Type hints present
- [ ] Documentation updated

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Documentation

## Testing
- [ ] Unit tests added
- [ ] Integration tests pass
- [ ] Performance tests pass

## Screenshots
(if applicable)
```

---

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org)
- [Qdrant API Docs](https://qdrant.tech/documentation)
- [OpenAI API Docs](https://platform.openai.com/docs)

---

**Questions? Open an issue on GitHub or contact the team!**
