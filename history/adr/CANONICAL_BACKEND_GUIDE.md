# Canonical Backend Guide

## Official Backend: `backend_v3/`

The **canonical and production-ready backend** for the Physical AI & Humanoid Robotics Textbook RAG chatbot is:

```
backend_v3/
```

**All other backend implementations are deprecated.**

---

## Why backend_v3?

### Production-Ready Features

✅ **OpenAI Agents SDK / ChatKit**
- Framework-based agent runtime
- System instructions for strict grounding
- Built-in conversation context management

✅ **Dual Database Support**
- SQLite for local development (automatic, no config)
- Neon Serverless Postgres for production (scalable)
- Same API, automatic detection

✅ **Strict Grounding Enforcement**
- Agent answers only from retrieved content
- Explicit refusals when context insufficient
- Temperature=0 for deterministic responses

✅ **Dual Retrieval Modes**
- Normal mode: Broad search (k=5, threshold=0.7)
- Selected-text mode: Constrained search (k=3, threshold=0.85)

✅ **Comprehensive Error Handling**
- Custom exception hierarchy
- Structured JSON logging
- Graceful degradation

✅ **Session Management**
- UUID-based sessions
- Conversation history (last 3 turns)
- Persistent across requests

---

## Quick Start

### 1. Navigate to Canonical Backend

```bash
cd backend_v3
```

### 2. Install Dependencies

Using pip:
```bash
pip install -r requirements.txt
```

Or using the included `pyproject.toml`:
```bash
pip install -e .
```

### 3. Configure Environment

Create `.env` file in `backend_v3/`:

```bash
# Required - OpenAI API
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Required - Qdrant Vector Database
QDRANT_URL=https://your-qdrant-instance.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key

# Optional - Database (uses SQLite if not set)
DATABASE_URL=postgresql://user:pass@neon.tech:5432/dbname
SQLITE_DB_PATH=chatbot.db

# Required - Embeddings
GEMINI_API_KEY=your_gemini_api_key
USE_MOCK_EMBEDDINGS=false

# Optional - API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### 4. Run the Server

```bash
python main.py
```

Server starts on `http://localhost:8000`

### 5. Verify Health

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{"status": "healthy"}
```

### 6. Test Chat Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is ROS 2?",
    "retrieval_mode": "normal"
  }'
```

---

## API Endpoints

### POST /api/v1/chat

Main chat endpoint for question answering.

**Request**:
```json
{
  "session_id": "optional-session-id",
  "question": "What is ROS 2?",
  "retrieval_mode": "normal",
  "selected_text": null
}
```

**Response**:
```json
{
  "session_id": "session-1704268800000-abc123",
  "answer": "ROS 2 is the next generation of the Robot Operating System... [Chapter 1, Section 1.2]",
  "citations": [
    {
      "chapter": "Chapter 1",
      "section": "Section 1.2",
      "text_snippet": "ROS 2 is the next generation...",
      "score": 0.85
    }
  ],
  "retrieval_mode": "normal",
  "grounded": true,
  "metadata": {
    "latency_ms": 2345.67,
    "num_chunks": 5,
    "is_refusal": false
  }
}
```

### POST /api/v1/sessions

Create a new conversation session.

**Response**:
```json
{
  "session_id": "session-1704268800000-abc123",
  "created_at": "2026-01-03T12:34:56Z"
}
```

### GET /api/v1/sessions/{session_id}

Get conversation history for a session.

**Response**:
```json
{
  "session_id": "session-123",
  "turns": [
    {
      "question": "What is ROS 2?",
      "answer": "ROS 2 is...",
      "created_at": "2026-01-03T12:34:56Z"
    }
  ]
}
```

### GET /api/v1/health

Health check endpoint.

**Response**:
```json
{"status": "healthy"}
```

---

## Directory Structure

```
backend_v3/
├── __init__.py                 Package initialization
├── main.py                     FastAPI application entry point
├── config.py                   Configuration management
├── requirements.txt            Python dependencies
├── pyproject.toml              Project metadata
├── README.md                   Detailed documentation
│
├── agent/                      Agent layer
│   ├── __init__.py             Agent exports
│   ├── chatkit_agent.py        OpenAI Agents SDK wrapper
│   ├── context_formatter.py    Context formatting for agent
│   ├── selected_text_handler.py Selected-text mode logic
│   └── answer_generator.py     Answer generation + validation
│
├── api/                        API layer
│   ├── __init__.py             API exports
│   └── routes.py               FastAPI endpoints
│
├── storage/                    Storage layer
│   ├── __init__.py             Storage exports
│   └── database.py             SQLite + Neon Postgres abstraction
│
└── utils/                      Utilities
    ├── __init__.py             Utils exports
    ├── error_handling.py       Custom exceptions
    └── logging.py              Structured JSON logging
```

---

## Configuration Options

### Database Configuration

**SQLite (Default)**:
- Automatically used if `DATABASE_URL` not set
- File: `chatbot.db` (or value of `SQLITE_DB_PATH`)
- Good for: Local development, testing

**Neon Postgres (Production)**:
- Set `DATABASE_URL` to Neon connection string
- Format: `postgresql://user:pass@neon.tech:5432/dbname`
- Good for: Production, scalable deployments

### Model Configuration

**OpenAI Models**:
- `gpt-4-turbo-preview` (default) - Best quality, higher latency
- `gpt-3.5-turbo` - Faster responses, lower cost

Set in `.env`:
```bash
OPENAI_MODEL=gpt-4-turbo-preview
```

### Retrieval Configuration

Configured in `retrieval/config.py`:

**Normal Mode**:
- `retrieval_top_k=5` (top 5 chunks)
- `retrieval_score_threshold=0.7` (70% relevance)

**Selected-Text Mode**:
- `selected_text_top_k=3` (top 3 chunks)
- `selected_text_score_threshold=0.85` (85% relevance)

---

## Deployment

### Local Development

```bash
cd backend_v3
python main.py
```

Runs on `http://localhost:8000`

### Production (Railway)

1. **Create Railway project**
2. **Set environment variables** in Railway dashboard:
   ```
   OPENAI_API_KEY
   QDRANT_URL
   QDRANT_API_KEY
   DATABASE_URL (Neon Postgres)
   GEMINI_API_KEY
   ```
3. **Deploy**:
   ```bash
   railway up
   ```
4. **Verify health**:
   ```bash
   curl https://your-app.railway.app/api/v1/health
   ```

### Production (Render)

1. **Create Render web service**
2. **Set environment variables** in Render dashboard
3. **Deploy** from GitHub repository
4. **Set start command**: `python backend_v3/main.py`

---

## Testing

### Quick Test

```bash
cd backend_v3
python -c "
from config import Config
from agent import ChatKitAgent, AnswerGenerator
print('✅ All imports successful')
"
```

### Integration Test

```bash
cd ..
python test_agentic_rag.py
```

This tests:
- Full-book question flow
- Selected-text question flow
- Refusal handling
- Database persistence

---

## Performance

### Typical Latency (P95)

```
API Validation:          ~10ms
Retrieval (Qdrant):      ~500ms
Context Formatting:      ~40ms
ChatKit Agent (OpenAI):  ~2500ms
Answer Validation:       ~50ms
Database Storage:        ~200ms
──────────────────────────────
Total:                   ~3.3 seconds
```

Target: <5 seconds ✅
Actual: ~3.3 seconds ✅

### Optimization Tips

1. **Use GPT-3.5-turbo** for faster responses (trade-off: quality)
2. **Enable caching** for frequent questions
3. **Use mock embeddings** in tests (`USE_MOCK_EMBEDDINGS=true`)
4. **Connection pooling** for Neon Postgres

---

## Troubleshooting

### "Agent not initialized"

**Cause**: `OPENAI_API_KEY` not set or invalid

**Solution**:
```bash
# Check .env file
cat backend_v3/.env | grep OPENAI_API_KEY

# Verify key format
# Should start with: sk-proj-... or sk-...
```

### "Database error"

**For Neon Postgres**:
```bash
# Check DATABASE_URL format
# Should be: postgresql://user:pass@host:5432/dbname

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

**For SQLite**:
```bash
# Check file permissions
ls -la chatbot.db

# Delete and recreate if corrupted
rm chatbot.db
python main.py  # Will recreate on startup
```

### "Retrieval failed"

**Cause**: Qdrant credentials or connectivity issue

**Solution**:
```bash
# Verify credentials
echo $QDRANT_URL
echo $QDRANT_API_KEY

# Test Qdrant connection
curl -X GET "$QDRANT_URL/collections/data_collection" \
  -H "api-key: $QDRANT_API_KEY"
```

### Empty or irrelevant responses

**Cause**: No content in Qdrant or poor retrieval

**Solution**:
```bash
# Check if book content ingested
cd ingestion
python test_search.py

# Re-ingest if needed
python ingest_book.py
```

---

## Deprecated Backends

### ⚠️ DO NOT USE

The following backend implementations are **deprecated**:

- `backend/` - Step 2 implementation (OpenRouter + Claude)
  - **Status**: Deprecated 2026-01-03
  - **See**: `backend/DEPRECATED.md`

**Always use `backend_v3/` for all current and future work.**

---

## Documentation

### Quick References

- **README**: `backend_v3/README.md` - Usage and API
- **Specification**: `specs/AGENTIC_RAG_SPEC.md` - Full spec
- **Completion**: `specs/AGENTIC_RAG_COMPLETE.md` - Implementation summary
- **Architecture**: `specs/AGENTIC_RAG_ARCHITECTURE.md` - Architecture details

### Comprehensive Guides

- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md`
- **Project Analysis**: `PROJECT_ANALYSIS.md`
- **Chat Widget Integration**: `CHAT_WIDGET_INTEGRATION.md`

---

## Version History

- **v3.0.0** (Current) - Agentic RAG with OpenAI Agents SDK / ChatKit
  - Location: `backend_v3/`
  - Status: ✅ Production-ready, canonical
  - Features: ChatKit, dual database, strict grounding

- **v2.0.0** (Deprecated) - RAG with OpenRouter + Claude
  - Location: `backend/`
  - Status: ⚠️ Deprecated 2026-01-03
  - Features: Custom orchestration, in-memory sessions

- **v1.0.0** - Ingestion pipeline only
  - Location: `ingestion/`
  - Status: ✅ Still active (for data ingestion)
  - Features: Qdrant ingestion, Gemini embeddings

---

## Support

**For Issues**:
1. Check this guide first
2. Review `backend_v3/README.md`
3. Check `PROJECT_ANALYSIS.md` for known issues
4. Review error logs in console output

**For Questions**:
- See comprehensive documentation in `specs/`
- Check `IMPLEMENTATION_SUMMARY.md` for deployment

---

**Last Updated**: 2026-01-03
**Canonical Backend**: `backend_v3/`
**Version**: 3.0.0
**Status**: ✅ **PRODUCTION-READY**
