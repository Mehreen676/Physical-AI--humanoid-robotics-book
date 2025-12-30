# Quick Start Guide: BookRAGAgent

**Date**: 2025-12-30 | **Status**: Phase 1 Design | **Target**: Local Development

---

## Overview

This guide walks you through setting up and running the BookRAGAgent locally for development and testing.

---

## Prerequisites

- **Python 3.11+** (check with `python --version`)
- **pip** or **uv** (modern package manager)
- **git** (for version control)
- **Accounts & API Keys**:
  - Qdrant Cloud (free tier): https://cloud.qdrant.io/
  - OpenRouter: https://openrouter.ai/ (for LLM access)
  - Neon PostgreSQL: https://neon.tech/ (free tier)

---

## Step 1: Clone & Setup Environment

### 1a. Clone Repository

```bash
git clone https://github.com/your-org/book-rag-chatbot.git
cd book-rag-chatbot
```

### 1b. Create Python Virtual Environment

```bash
# Using venv
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

Or using uv (faster):

```bash
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

---

## Step 2: Install Dependencies

### 2a. Install Python Packages

```bash
cd backend
pip install -r requirements.txt
```

**Or with uv**:

```bash
uv pip install -r requirements.txt
```

### 2b. Verify Installation

```bash
python -c "import fastapi; import qdrant_client; import psycopg2; print('All dependencies installed successfully')"
```

---

## Step 3: Configure Environment Variables

### 3a. Create .env File

Copy the template and fill in your credentials:

```bash
cp .env.example .env
```

### 3b. Edit .env with Your Credentials

```bash
# .env file (NEVER commit this file)

# Vector Database (Qdrant Cloud)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
COLLECTION_NAME=book-chunks

# LLM Provider (OpenRouter)
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_URL=https://openrouter.io
MODEL_NAME=claude-3-5-sonnet

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@region.neon.tech/dbname

# Server
BASE_URL=http://localhost:8000
```

### 3c. Get Your API Keys

**Qdrant Cloud**:
1. Sign up at https://cloud.qdrant.io/
2. Create a free cluster
3. Copy the API key from dashboard

**OpenRouter**:
1. Sign up at https://openrouter.ai/
2. Generate API key in account settings
3. Add credits (or use free tier)

**Neon PostgreSQL**:
1. Sign up at https://neon.tech/
2. Create a new project
3. Copy connection string from dashboard

---

## Step 4: Initialize Database

### 4a. Create Tables

```bash
# Run from backend directory
python -m alembic upgrade head
```

Or manually using psycopg2:

```python
# backend/db/init.py
python -c "
from backend.db.init import init_db
init_db()
print('Database initialized successfully')
"
```

### 4b. Verify Database Connection

```bash
python -c "
import psycopg2
from backend.config import settings
conn = psycopg2.connect(settings.database_url)
cursor = conn.cursor()
cursor.execute('SELECT 1')
print('Database connection successful')
cursor.close()
conn.close()
"
```

---

## Step 5: (Optional) Populate Qdrant with Book Chunks

If you have a pre-embedded book:

```bash
# Load book chunks into Qdrant
python -m backend.scripts.load_book_chunks --collection-name book-chunks --chunks-file data/chunks.json
```

Or use the test fixtures for development:

```bash
python -m backend.scripts.load_test_fixtures
```

---

## Step 6: Run the Server

### 6a. Start FastAPI Development Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 6b. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Step 7: Test the API

### 7a. Create a Session

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json"
```

**Response**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-12-30T12:34:56Z"
}
```

### 7b. Ask a Question

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Chapter 3 about?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "selected_text": null
  }'
```

**Response**:
```json
{
  "answer": "Chapter 3 focuses on neural network fundamentals...",
  "citations": [
    {
      "section": "Chapter 3: Neural Networks",
      "url": "https://book.example.com/chapter-3"
    }
  ],
  "retrieved_chunks": [
    {
      "text": "Chapter 3 provides a comprehensive introduction...",
      "metadata": {
        "url": "https://book.example.com/chapter-3",
        "section": "Chapter 3: Neural Networks",
        "chunk_id": "chunk-00042",
        "position": 1,
        "embedding_score": 0.8754
      }
    }
  ]
}
```

### 7c. Get Session History

```bash
curl -X GET http://localhost:8000/sessions/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json"
```

### 7d. Health Check

```bash
curl -X GET http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "qdrant": "ok",
    "database": "ok",
    "openrouter": "ok"
  }
}
```

---

## Step 8: Run Tests

### 8a. Unit Tests

```bash
pytest tests/unit/ -v
```

### 8b. Integration Tests

```bash
pytest tests/integration/ -v
```

### 8c. Full Test Suite

```bash
pytest --cov=backend tests/
```

---

## Step 9: Enable Debug Logging

To see detailed logs for debugging:

```bash
# Set log level in .env
LOG_LEVEL=DEBUG

# Or set in code before starting server
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Troubleshooting

### Issue: "Missing required environment variable: OPENROUTER_API_KEY"

**Solution**:
1. Check that .env file exists in `backend/` directory
2. Verify all required variables are set
3. Run: `python -c "from backend.config import settings; print('Config loaded')"` to validate

### Issue: "Qdrant connection refused"

**Solution**:
1. Check QDRANT_URL is correct (format: `https://cluster-name.qdrant.io`)
2. Verify QDRANT_API_KEY is valid
3. Test: `curl https://your-cluster.qdrant.io/health -H "api-key: your-key"`

### Issue: "Database connection failed"

**Solution**:
1. Verify DATABASE_URL format: `postgresql://user:password@host:port/dbname`
2. Check password for special characters (URL-encode if needed)
3. Test: `psql <DATABASE_URL>` to verify connection

### Issue: "Collection 'book-chunks' does not exist in Qdrant"

**Solution**:
1. Create collection manually via Qdrant dashboard, OR
2. Load test fixtures: `python -m backend.scripts.load_test_fixtures`

---

## Common Commands

```bash
# Start server with reload (development)
uvicorn backend.main:app --reload

# Start server without reload (production)
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest --cov=backend tests/

# Format code
black backend/ tests/

# Lint code
flake8 backend/ tests/

# Type checking
mypy backend/

# Stop server (Ctrl+C in terminal)
```

---

## Docker Setup (Optional)

### Build Docker Image

```bash
docker build -f docker/Dockerfile -t book-rag-agent:latest .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e QDRANT_URL=https://your-cluster.qdrant.io \
  -e QDRANT_API_KEY=your-key \
  -e OPENROUTER_API_KEY=your-key \
  -e DATABASE_URL=postgresql://... \
  book-rag-agent:latest
```

---

## Next Steps

1. **Run the test suite** to ensure everything works
2. **Explore the Swagger UI** at http://localhost:8000/docs
3. **Review the implementation plan** in `specs/006-book-rag-agent/plan.md`
4. **Follow the task breakdown** in `specs/006-book-rag-agent/tasks.md`

---

## Support

For issues or questions:
1. Check the logs: `LOG_LEVEL=DEBUG` in .env
2. Review error messages in API responses
3. Check `/health` endpoint to see which services are failing
4. See main README.md for architecture overview

---

**Ready to start implementing?** Run `/sp.tasks` to generate the task breakdown.
