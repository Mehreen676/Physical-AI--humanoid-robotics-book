# Agentic RAG Chatbot - ChatKit Implementation

Production-ready RAG chatbot using **OpenAI Agents SDK / ChatKit** with strict grounding validation.

## Overview

This implementation (v3.0.0) uses OpenAI's Agents SDK (ChatKit) for agent-based reasoning over book content, enforcing strict grounding rules to prevent hallucinations.

### Key Features

- **OpenAI Agents SDK / ChatKit**: Framework-based agent runtime
- **Strict Grounding**: All answers must be sourced from retrieved content
- **Explicit Refusals**: Clear "cannot answer" when context insufficient
- **Dual Retrieval Modes**: Normal (broad) and selected-text (constrained)
- **Persistent History**: SQLite (local) or Neon Postgres (production)
- **Deterministic Responses**: Temperature=0 for reproducible outputs

## Architecture

```
User → FastAPI → Retrieval Layer → Context Formatter →
ChatKit Agent → Answer Generator → Database → Response
```

### Components

1. **Retrieval Layer** (reused from Step 1 & 2)
   - Semantic search via Qdrant
   - Gemini embeddings
   - Mode: normal vs selected-text

2. **ChatKit Agent** (new)
   - OpenAI Agents SDK
   - System instructions enforcing grounding
   - Temperature=0 for determinism

3. **Context Formatter** (new)
   - Formats chunks for agent consumption
   - Adds metadata (chapter, section)
   - Handles selected-text mode

4. **Answer Generator** (new)
   - Generates grounded answers
   - Detects refusals
   - Extracts citations
   - Validates grounding

5. **Database** (new)
   - SQLite for local development
   - Neon Postgres for production
   - Session and turn persistence

## Quick Start

### 1. Install Dependencies

```bash
pip install openai fastapi uvicorn pydantic python-dotenv
```

### 2. Configure Environment

```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_key

# Optional (uses SQLite if not set)
DATABASE_URL=postgresql://user:pass@neon.tech/dbname

# Embeddings (or use mock)
GEMINI_API_KEY=your_gemini_key
USE_MOCK_EMBEDDINGS=false
```

### 3. Run Server

```bash
cd backend_v3
python main.py
```

Server runs on `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### 4. Test

```bash
python test_agentic_rag.py
```

## API Endpoints

### POST /api/v1/chat

Main chat endpoint.

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
  "session_id": "abc-123",
  "answer": "ROS 2 is the next generation... [Chapter 1, Section 1.2]",
  "citations": [
    {
      "chapter": "Chapter 1",
      "section": "Section 1.2",
      "text_snippet": "...",
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

Create new conversation session.

### GET /api/v1/sessions/{session_id}

Get conversation history.

### GET /api/v1/health

Health check.

## Grounding Rules

The ChatKit agent enforces strict grounding through system instructions:

```
CRITICAL GROUNDING RULES:
1. Use ONLY the provided context to answer questions
2. If answer not in context, respond: "I cannot answer this question based on the book content provided."
3. Do NOT use external knowledge or prior information
4. Do NOT infer, speculate, or extrapolate beyond context
5. Cite chapter and section: [Chapter X, Section Y]
6. Keep answers concise
7. Acknowledge uncertainty if context ambiguous
```

## Retrieval Modes

### Normal Mode
- Broad semantic search
- top_k=5, threshold=0.7
- Good for general questions

### Selected-Text Mode
- User highlights specific passage
- Retrieval constrained to selection
- top_k=3, threshold=0.85
- High precision answers

**Example**:
```json
{
  "question": "Explain this concept",
  "retrieval_mode": "selected_text",
  "selected_text": "DDS is used for inter-node communication"
}
```

## Database Storage

### SQLite (Default)

Used automatically if `DATABASE_URL` not set.

```bash
SQLITE_DB_PATH=chatbot.db
```

### Neon Postgres (Production)

Set `DATABASE_URL` to use Neon Serverless Postgres:

```bash
DATABASE_URL=postgresql://user:pass@neon.tech:5432/dbname
```

**Schema**:
```sql
-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat turns table
CREATE TABLE chat_turns (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    question TEXT NOT NULL,
    retrieval_mode VARCHAR(20) NOT NULL,
    context_chunk_ids TEXT[],
    answer TEXT NOT NULL,
    grounded BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| OPENAI_API_KEY | OpenAI API key (required) | - |
| OPENAI_MODEL | Model to use | gpt-4-turbo-preview |
| DATABASE_URL | Neon Postgres URL (optional) | - |
| SQLITE_DB_PATH | SQLite database path | chatbot.db |
| QDRANT_URL | Qdrant instance URL (required) | - |
| QDRANT_API_KEY | Qdrant API key (required) | - |
| GEMINI_API_KEY | Gemini API key (required if not using mock) | - |
| USE_MOCK_EMBEDDINGS | Use mock embeddings | false |
| API_HOST | API server host | 0.0.0.0 |
| API_PORT | API server port | 8000 |

## Performance

**Typical Latency** (P95):
- Retrieval: ~500ms
- Context formatting: ~40ms
- Agent processing: ~2.5s (OpenAI API call)
- Database storage: ~200ms
- **Total**: ~3.3 seconds

**Optimization**:
- Set `USE_MOCK_EMBEDDINGS=true` for faster testing
- Use connection pooling for Neon Postgres
- Cache identical questions (deterministic responses)

## Error Handling

- **400**: Invalid request (validation errors)
- **404**: Session not found
- **500**: Internal server error

Database errors don't fail the request - answer still returned, but turn not persisted.

## Comparison to Step 2 (Claude via OpenRouter)

| Feature | Step 2 (OpenRouter) | Step 3 (ChatKit) |
|---------|---------------------|------------------|
| Agent Framework | Custom orchestration | OpenAI Agents SDK |
| Model | Claude 3.5 Sonnet | GPT-4 Turbo |
| Storage | In-memory | SQLite / Neon Postgres |
| Grounding | Manual validation | System instructions |
| Conversation | Manual history | Built-in context |

## Testing

```bash
# Run test script
python test_agentic_rag.py
```

**Tests**:
1. Simple question (normal mode)
2. Selected-text mode
3. Out-of-scope question (refusal)
4. Database persistence

## Deployment

### Local Development

```bash
python backend_v3/main.py
```

### Production (Railway / Render)

1. Set environment variables
2. Connect Neon Postgres
3. Deploy `backend_v3/main.py`
4. Health check: `/api/v1/health`

## Troubleshooting

**"Agent not initialized"**
- Check OPENAI_API_KEY is set
- Verify API key is valid

**"Database error"**
- For Neon: Check DATABASE_URL format
- For SQLite: Check file permissions

**"Retrieval failed"**
- Verify QDRANT_URL and QDRANT_API_KEY
- Check Qdrant cluster is running

**Empty responses**
- Check retrieval returns chunks
- Verify agent isn't refusing due to no context

## Version

**3.0.0** - Agentic RAG with OpenAI Agents SDK / ChatKit

Built on top of:
- Step 1: Ingestion (Qdrant + embeddings)
- Step 2: Retrieval layer (semantic search)
