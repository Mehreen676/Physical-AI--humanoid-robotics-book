# RAG Chatbot Backend

Production-ready FastAPI backend for Integrated Retrieval-Augmented Generation (RAG) Chatbot embedded in Docusaurus.

## Overview

This backend provides RESTful APIs for:
- **Content Ingestion**: Upload and embed book chapters
- **Semantic Retrieval**: Find relevant content using vector similarity
- **Response Generation**: Generate answers using OpenAI GPT-4o
- **Session Management**: Persist chat history and user sessions

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required:
- `OPENAI_API_KEY`: Your OpenAI API key
- `QDRANT_URL` & `QDRANT_API_KEY`: Qdrant Cloud credentials
- `DATABASE_URL`: Neon PostgreSQL connection string

### 3. Run Backend Server

```bash
cd src
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server runs at `http://localhost:8000`

### 4. Check Health

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-16T19:45:30.123456",
  "version": "1.0.0",
  "environment": "development"
}
```

## Project Structure

```
rag-backend/
├── src/
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration management
│   ├── __init__.py
│   ├── database/         # Database models & session
│   ├── agents/           # RAG agents (retrieval, generation)
│   ├── api/              # API route handlers
│   └── utils/            # Helper functions
├── sdk/
│   └── chat-embed.js    # JavaScript client library
├── tests/
│   ├── test_health.py   # Health endpoint tests
│   └── ...
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
└── README.md
```

## API Endpoints

### Health Check
- `GET /health` - Server status

### Ingestion
- `POST /ingest` - Upload and embed chapters

### Queries
- `POST /query` - Query full book (RAG mode)
- `POST /query-selected-text` - Query with highlighted text only

### Sessions
- `GET /sessions/{session_id}` - Get chat history

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Run Specific Test

```bash
pytest tests/test_health.py::test_health_check -v
```

## Configuration

All settings loaded from environment variables (`.env` file):

- `DEBUG` - Enable debug mode
- `OPENAI_API_KEY` - OpenAI API key
- `QDRANT_URL` - Qdrant instance URL
- `DATABASE_URL` - PostgreSQL connection string
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING)

## Performance Targets

- **Retrieval Latency**: ≤ 500ms (p95)
- **Generation Latency**: ≤ 5s (p95)
- **Total Latency**: ≤ 6s (p95)
- **RAG Accuracy**: ≥ 90%
- **Error Rate**: < 1%

## Cost Budget

Monthly estimates (typical usage: 500-1000 queries):
- Qdrant Cloud: $0 (free tier)
- Neon PostgreSQL: $0 (free tier)
- OpenAI Embeddings: ~$2
- OpenAI GPT-4o: ~$10-30
- Hosting: $0-5
- **Total**: $12-40/month

## Related Documentation

- [Feature Specification](../specs/2-rag-chatbot-integration/spec.md)
- [Implementation Plan](../specs/2-rag-chatbot-integration/plan.md)
- [Architecture Decision Records](../history/adr/)

## License

Part of Physical AI & Humanoid Robotics Textbook project.
