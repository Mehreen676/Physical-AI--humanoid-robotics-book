# Physical AI & Humanoid Robotics Textbook - RAG Chatbot

A complete agentic RAG (Retrieval-Augmented Generation) system for an interactive educational textbook with embedded chat interface.

## Features

- **Agentic RAG Backend**: Multi-agent system with strict grounding (OpenAI Agents SDK / ChatKit)
- **Embedded Chat Widget**: React-based interface integrated directly into Docusaurus book
- **Hallucination-Free Q&A**: Answers grounded exclusively in retrieved book content
- **Dual Retrieval Modes**: Normal (full-book) and selected-text (constrained) search
- **Multi-Turn Conversations**: Session management with conversation history
- **Dual Database Support**: SQLite (local) + Neon Serverless Postgres (production)
- **Production-Ready**: Comprehensive error handling, logging, and deployment guides

## Backend

The canonical and production-ready backend is located in **`backend_v3/`**. See [CANONICAL_BACKEND_GUIDE.md](CANONICAL_BACKEND_GUIDE.md) for complete documentation.

## Project Structure

```
text-book/
├── backend_v3/                 # Production-ready backend
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration management
│   ├── requirements.txt        # Python dependencies
│   ├── models/                 # Pydantic schemas
│   ├── agent/                  # ChatKit agent + answer generation
│   ├── api/                    # FastAPI routes
│   ├── storage/                # SQLite + Neon Postgres
│   └── utils/                  # Error handling + logging
│
├── front-end/                  # Docusaurus book + chat widget
│   ├── docs/                   # Book content (MDX)
│   └── src/components/ChatWidget/  # Embedded chat interface
│
├── retrieval/                  # Standalone retrieval layer
│   ├── retriever.py            # Semantic search (Qdrant)
│   ├── embeddings.py           # Gemini embeddings
│   └── qdrant_client.py        # Vector database client
│
├── ingestion/                  # Book content ingestion
│   ├── ingest_book.py          # Main ingestion script
│   └── test_search.py          # Search validation
│
└── docs/                       # Documentation
    ├── CANONICAL_BACKEND_GUIDE.md  # Backend setup guide
    ├── IMPLEMENTATION_SUMMARY.md   # Deployment guide
    └── PROJECT_ANALYSIS.md         # Complete project analysis
```

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Qdrant Cloud account
- OpenAI API key
- Gemini API key (for embeddings)

### Backend Setup

1. **Navigate to canonical backend**:
   ```bash
   cd backend_v3
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   Create `.env` file in `backend_v3/`:
   ```bash
   OPENAI_API_KEY=sk-your-openai-key-here
   OPENAI_MODEL=gpt-4-turbo-preview
   QDRANT_URL=https://your-qdrant-instance.cloud.qdrant.io:6333
   QDRANT_API_KEY=your_qdrant_api_key
   GEMINI_API_KEY=your_gemini_api_key

   # Optional - uses SQLite if not set
   DATABASE_URL=postgresql://user:pass@neon.tech:5432/dbname
   ```

4. **Start the backend**:
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`

5. **Test endpoints**:
   ```bash
   # Health check
   curl http://localhost:8000/api/v1/health

   # Create a session
   curl -X POST http://localhost:8000/api/v1/sessions

   # Send a question
   curl -X POST http://localhost:8000/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"question": "What is ROS 2?", "retrieval_mode": "normal"}'
   ```

### Frontend Setup

1. **Navigate to frontend**:
   ```bash
   cd front-end
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure backend URL**:
   Create `.env` file in `front-end/`:
   ```bash
   CHATBOT_BACKEND_URL=http://localhost:8000
   ```

4. **Start Docusaurus**:
   ```bash
   npm start
   ```

   The book will open at `http://localhost:3000`

5. **Test chat widget**:
   - Look for chat button in bottom-right corner
   - Click to open chat panel
   - Type a question and press Enter
   - Verify response appears with citations

## Deployment

### Backend Deployment (Railway/Render)

#### Prerequisites

1. GitHub repository
2. Railway or Render account
3. Environment variables:
   - `OPENAI_API_KEY` (required)
   - `QDRANT_URL` (required)
   - `QDRANT_API_KEY` (required)
   - `GEMINI_API_KEY` (required)
   - `DATABASE_URL` (optional - uses SQLite if not set)
   - `OPENAI_MODEL` (optional - defaults to gpt-4-turbo-preview)

#### Railway Deployment

1. **Create Railway project**
2. **Connect GitHub repository**
3. **Set environment variables** in Railway dashboard
4. **Deploy**:
   ```bash
   cd backend_v3
   railway up
   ```
5. **Verify deployment**:
   ```bash
   curl https://your-app.railway.app/api/v1/health
   ```

#### Render Deployment

1. **Create Render web service**
2. **Connect GitHub repository**
3. **Set root directory**: `backend_v3`
4. **Set start command**: `python main.py`
5. **Set environment variables** in Render dashboard
6. **Deploy** (automatic on push to main branch)
7. **Verify deployment**:
   ```bash
   curl https://your-app.onrender.com/api/v1/health
   ```

### Frontend Deployment (GitHub Pages)

#### Prerequisites

1. Backend deployed and accessible
2. GitHub Pages enabled for repository
3. Environment variable `CHATBOT_BACKEND_URL` set in GitHub Secrets

#### Deployment Steps

1. **Set GitHub Secret**:
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Add `CHATBOT_BACKEND_URL` with your backend URL

2. **Update backend CORS** in `backend_v3/config.py`:
   ```python
   CORS_ORIGINS = [
       "https://your-username.github.io",  # Production
   ]
   ```

3. **Build and deploy**:
   ```bash
   cd front-end
   npm run build
   npm run deploy
   ```

4. **Verify deployment**:
   - Visit your GitHub Pages URL
   - Test chat widget functionality


## API Endpoints

### Health Check
```
GET /api/v1/health
Response: { "status": "healthy" }
```

### Sessions
```
POST /api/v1/sessions
Response: { "session_id": "session-123", "created_at": "2026-01-03T..." }

GET /api/v1/sessions/{session_id}
Response: {
  "session_id": "session-123",
  "turns": [{"question": "...", "answer": "...", "created_at": "..."}]
}
```

### Chat
```
POST /api/v1/chat
Body: {
  "session_id": "session-123",
  "question": "What is ROS 2?",
  "retrieval_mode": "normal",
  "selected_text": null
}
Response: {
  "session_id": "session-123",
  "answer": "ROS 2 is... [Chapter 1, Section 1.2]",
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
    "latency_ms": 3300,
    "num_chunks": 5,
    "is_refusal": false
  }
}
```

## Configuration

### Backend Environment Variables

See `backend_v3/.env.example` for complete list. Key variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key (sk-...) |
| `QDRANT_URL` | Yes | - | Qdrant Cloud URL |
| `QDRANT_API_KEY` | Yes | - | Qdrant API key |
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `DATABASE_URL` | No | SQLite | Neon Postgres connection string |
| `OPENAI_MODEL` | No | gpt-4-turbo-preview | OpenAI model to use |
| `API_HOST` | No | 0.0.0.0 | API host binding |
| `API_PORT` | No | 8000 | API port |
| `LOG_LEVEL` | No | INFO | Logging level |

### Frontend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CHATBOT_BACKEND_URL` | Yes | http://localhost:8000 | Backend API URL |

## Troubleshooting

### Docker Build Issues

**Error**: `permission denied while trying to connect to Docker daemon`
- Solution: Install Docker or use Render's Docker hosting

**Error**: `ModuleNotFoundError: No module named 'backend'`
- Solution: Ensure PYTHONPATH includes parent directory or use relative imports

### Render Deployment Issues

**Build Fails**: Check logs in Render Dashboard
- Ensure `Dockerfile` exists in repo root
- Verify all environment variables are set

**Service Crashes**:
- Check logs: Render → Logs tab
- Verify `DATABASE_URL` and `QDRANT_URL` are accessible
- Ensure `OPENROUTER_API_KEY` is valid

**Port Issues**:
- Render automatically maps port 10000
- Don't override with environment variables

## Development

### Running Tests

```bash
cd backend_v3
pytest tests/ -v --cov=.
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

## License

MIT

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check existing documentation in `/specs`
- Review ARCHITECTURE.md for technical details
