# BookRAGAgent - Hallucination-Free RAG Chatbot

A FastAPI-based backend for a hallucination-free RAG (Retrieval-Augmented Generation) chatbot that answers questions about book content using Qdrant vector database and Claude 3.5 Sonnet LLM.

## Features

- **Hallucination-Free Q&A**: Answers are grounded exclusively in retrieved book content
- **Vector Search**: Semantic search using Qdrant vector database
- **Multi-Turn Conversations**: Session management with conversation history
- **Selected Text Mode**: Focus retrieval on user-selected passages
- **FastAPI Backend**: Async REST API with comprehensive error handling
- **Docker Ready**: Production-ready containerization for Render deployment

## Project Structure

```
text-book/
├── backend/                    # FastAPI backend application
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration management
│   ├── requirements.txt         # Python dependencies
│   ├── agent/                  # RAG agent and sub-agents
│   ├── rag/                    # Retrieval and grounding skills
│   ├── api/                    # API routes
│   ├── services/               # External service integrations
│   ├── storage/                # Database models and session management
│   ├── models/                 # Pydantic schemas
│   └── utils/                  # Utility functions and error handling
├── Dockerfile                   # Production Docker image definition
├── render.yaml                  # Render deployment configuration
├── .dockerignore                # Docker build context exclusions
└── .env.example                 # Example environment variables
```

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- PostgreSQL (Neon)
- Qdrant Cloud
- OpenRouter API key

### Setup

1. **Clone and install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp ../.env.example ../.env
   # Edit .env with your API keys and database URLs
   ```

3. **Start the server**:
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`

4. **Test endpoints**:
   ```bash
   # Create a session
   curl -X POST http://localhost:8000/sessions

   # Check health
   curl http://localhost:8000/health
   ```

## Docker & Deployment

### Local Docker Testing

Build and run the Docker image locally:

```bash
# Build image
docker build -t bookrag:latest .

# Run container
docker run -p 10000:10000 \
  -e DATABASE_URL=postgresql://... \
  -e QDRANT_URL=https://... \
  -e QDRANT_API_KEY=... \
  -e OPENROUTER_API_KEY=... \
  bookrag:latest

# Test health endpoint
curl http://localhost:10000/health

# View logs
docker logs <container-id>
```

### Docker Image Details

- **Base Image**: `python:3.11-slim` (lightweight, secure)
- **Security**: Runs as non-root user (`appuser`)
- **Port**: 10000 (for Render PaaS)
- **Health Check**: GET `/health` endpoint
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`

### Render Deployment

#### Prerequisites

1. GitHub repository with Dockerfile
2. Render account (https://render.com)
3. Environment variables configured:
   - `DATABASE_URL` (PostgreSQL)
   - `QDRANT_URL` (Vector database)
   - `QDRANT_API_KEY`
   - `OPENROUTER_API_KEY`
   - `COLLECTION_NAME` (default: `book-chunks`)
   - `MODEL_NAME` (default: `claude-3-5-sonnet`)

#### Deployment Steps

1. **Connect GitHub Repository**:
   - Log in to Render Dashboard
   - Click "New +" → "Web Service"
   - Select your GitHub repository
   - Grant Render access to your repos

2. **Configure Service**:
   - **Name**: `bookrag-api`
   - **Environment**: Docker
   - **Region**: Oregon (or closest to you)
   - **Plan**: Starter or Standard

3. **Set Environment Variables**:
   - Click "Environment" tab
   - Add each required environment variable
   - **Critical**: Don't commit `.env` file - set in Render dashboard only

4. **Configure Build & Deploy**:
   - **Docker filepath**: `Dockerfile` (auto-detected)
   - **Auto-deploy**: Enable to auto-deploy on main branch push

5. **Deploy**:
   - Click "Create Web Service"
   - Wait for build to complete (2-3 minutes)
   - Render assigns unique URL (e.g., `https://bookrag-api.onrender.com`)

6. **Verify Deployment**:
   ```bash
   curl https://bookrag-api.onrender.com/health
   ```

#### Post-Deployment Verification

```bash
# Test health endpoint
curl https://your-service.onrender.com/health

# Create a session
curl -X POST https://your-service.onrender.com/sessions

# Check logs in Render Dashboard
# → Logs tab shows real-time server output
```

## API Endpoints

### Health Check
```
GET /health
Response: { "status": "healthy", "services": {...} }
```

### Sessions
```
POST /sessions
Response: { "session_id": "uuid", "created_at": "timestamp" }

GET /sessions/{session_id}
Response: { "session_id": "uuid", "messages": [...] }
```

### Chat
```
POST /chat
Body: {
  "session_id": "uuid",
  "question": "Your question here",
  "retrieval_mode": "normal"
}
Response: {
  "answer": "Grounded answer from book content",
  "citations": [{"section": "...", "url": "..."}]
}
```

## Environment Variables

See `.env.example` for complete list. Key variables:

| Variable | Required | Example |
|----------|----------|---------|
| `DATABASE_URL` | Yes | `postgresql://user:pass@host/db` |
| `QDRANT_URL` | Yes | `https://xxx.gcp.cloud.qdrant.io:6333` |
| `QDRANT_API_KEY` | Yes | `your-key-here` |
| `OPENROUTER_API_KEY` | Yes | `sk-or-xxx` |
| `COLLECTION_NAME` | No | `book-chunks` |
| `MODEL_NAME` | No | `claude-3-5-sonnet` |
| `PORT` | No | `10000` (Render) or `8000` (local) |

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
cd backend
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
