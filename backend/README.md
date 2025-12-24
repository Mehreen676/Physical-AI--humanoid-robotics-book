# Physical AI Textbook - Backend Service

FastAPI backend for the Physical AI & Humanoid Robotics interactive textbook.

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL (Neon or local)
- Qdrant vector database

### Setup

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp ../.env.example .env.local
   # Edit .env.local with your credentials
   ```

4. **Run the server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   Visit http://localhost:8000/api/docs for interactive API documentation

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── health.py     # Health check routes
│   │   ├── auth.py       # Authentication routes
│   │   ├── chat.py       # Chatbot routes (TODO)
│   │   └── content.py    # Content routes (TODO)
│   │
│   ├── models/           # SQLAlchemy ORM models
│   │   ├── user.py       # User and preferences
│   │   ├── chat.py       # Chat sessions and messages
│   │   └── content.py    # Chapters and progress
│   │
│   ├── schemas/          # Pydantic validation schemas
│   │   ├── auth.py       # Auth request/response
│   │   ├── chat.py       # Chat request/response
│   │   └── content.py    # Content request/response
│   │
│   ├── services/         # Business logic (TODO)
│   │   ├── rag.py        # RAG chatbot service
│   │   ├── embedding.py  # Embeddings service
│   │   └── personalize.py # Personalization service
│   │
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings from env vars
│   │   ├── database.py   # SQLAlchemy setup
│   │   ├── security.py   # JWT and password utilities
│   │   └── logging.py    # Structured logging
│   │
│   └── main.py           # FastAPI application
│
├── tests/                # Unit and integration tests (TODO)
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project metadata
└── README.md             # This file
```

## API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /api/health` - Detailed health (database, Qdrant status)

### Authentication
- `POST /api/auth/signup` - Create new user account
- `POST /api/auth/signin` - Login and get JWT token
- `POST /api/auth/logout` - Logout (invalidate token)
- `GET /api/auth/me` - Get current user profile
- `PUT /api/auth/me` - Update user profile

### Chat (Phase 1.3)
- `POST /api/chat/query` - Ask a question (RAG chatbot)
- `GET /api/chat/history` - Get chat history
- `GET /api/chat/sessions` - List user's chat sessions

### Content (Phase 1)
- `GET /api/chapters` - List all chapters
- `GET /api/chapters/{id}` - Get chapter content
- `GET /api/modules/{module}` - Get chapters by module

### Progress (Phase 1)
- `POST /api/progress` - Save chapter progress
- `GET /api/progress` - Get user's progress
- `GET /api/progress/{chapter_id}` - Get progress for chapter

### API Documentation
- `GET /api/docs` - Swagger UI (interactive docs)
- `GET /api/openapi.json` - OpenAPI schema

## Configuration

All configuration comes from environment variables (see `.env.example`):

### Database
- `DATABASE_URL` - PostgreSQL connection string (Neon format)

### Vector Database
- `QDRANT_URL` - Qdrant instance URL
- `QDRANT_API_KEY` - Qdrant API key (optional if local)

### Authentication
- `JWT_SECRET` - Secret key for JWT signing
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `JWT_EXPIRY_DAYS` - Token expiry (default: 30)

### AI/LLM
- `OPENAI_API_KEY` - OpenAI API key
- `OPENAI_MODEL` - Model name (default: gpt-4)
- `OPENAI_EMBEDDING_MODEL` - Embedding model (default: text-embedding-3-small)

### Email
- `SENDGRID_API_KEY` - SendGrid API key
- `SENDGRID_FROM_EMAIL` - From email address

### Server
- `SERVER_HOST` - Server host (default: 0.0.0.0)
- `SERVER_PORT` - Server port (default: 8000)
- `ENVIRONMENT` - Environment name (development/staging/production)
- `DEBUG` - Debug mode (default: true)
- `LOG_LEVEL` - Logging level (default: INFO)

## Development

### Run with auto-reload
```bash
uvicorn app.main:app --reload
```

### Run tests
```bash
pytest tests/ -v --cov=app
```

### Lint code
```bash
flake8 app/
black app/
isort app/
```

### Type checking
```bash
mypy app/
```

## Database Migrations

Using SQLAlchemy ORM (no Alembic yet):

```python
from app.core.database import init_db
init_db()  # Creates all tables
```

For schema changes:
1. Update model in `app/models/`
2. Call `init_db()` (creates new tables only)
3. For data migrations, add scripts in `backend/migrations/`

## Authentication Flow

1. **Signup**:
   ```
   POST /api/auth/signup
   → Create user (email, password hash)
   → Create preferences
   → Return JWT token
   ```

2. **Signin**:
   ```
   POST /api/auth/signin
   → Verify email + password
   → Create JWT token
   → Return token
   ```

3. **Protected requests**:
   ```
   GET /api/auth/me (Header: Authorization: Bearer <token>)
   → Decode JWT
   → Return user profile
   ```

## RAG Chatbot Pipeline (Phase 1.3)

```
User Query
  ↓
[Embedding Service]
  → OpenAI text-embedding-3-small
  → 1536 dimensions
  ↓
[Qdrant Retrieval]
  → Semantic search (cosine similarity)
  → Top-5 chunks
  ↓
[Ranking & Filter]
  → Re-rank by relevance
  → Filter low-confidence (< 0.7)
  ↓
[Context Augmentation]
  → Format chunks into context
  → Prepare for LLM
  ↓
[GPT-4 Generation]
  → System prompt + context + query
  → Generate answer
  ↓
[Response Filtering]
  → Validate grounded in sources
  → Add citations
  ↓
Response
```

## Testing

### Unit Tests
```bash
pytest tests/test_auth.py -v
pytest tests/test_models.py -v
```

### Integration Tests
```bash
pytest tests/test_api.py -v
```

### E2E Tests
```bash
pytest tests/test_e2e.py -v
```

## Deployment

### Local Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Railway/Vercel)
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables set in Railway/Vercel dashboard.

## Monitoring

### Logs
- Structured JSON logging to stdout
- Forwarded to platform (Railway, Vercel, Sentry)

### Health Checks
- `GET /health` - Used by load balancer
- `GET /api/health` - Detailed status

### Metrics (Phase 5)
- Request latency
- Error rates
- Database performance
- Qdrant query performance

## Troubleshooting

### Database Connection Error
```
Error: could not connect to server
```
- Check `DATABASE_URL` in `.env.local`
- Verify Neon credentials and IP whitelist
- Test: `psql $DATABASE_URL -c "SELECT 1"`

### Qdrant Connection Error
```
Error: Failed to connect to Qdrant
```
- Check `QDRANT_URL` and `QDRANT_API_KEY`
- Verify Qdrant is running (local) or accessible (cloud)
- Test: `curl $QDRANT_URL/health`

### JWT Token Error
```
Error: Invalid authentication credentials
```
- Token may have expired (30 days)
- Signin again to get new token
- Check `JWT_SECRET` matches on all instances

## Phase Checklist

- [x] Database models (User, Chat, Chapter, Progress)
- [x] Pydantic schemas (validation)
- [x] Authentication endpoints (signup, signin, logout)
- [x] Health check endpoints
- [ ] Chat endpoints (RAG chatbot) - Phase 1.3
- [ ] Content endpoints - Phase 1
- [ ] Progress endpoints - Phase 1
- [ ] Email service - Phase 0.5
- [ ] Error handling & validation - Phase 0.5
- [ ] Rate limiting - Phase 4
- [ ] Caching (Redis) - Phase 4
- [ ] Testing suite - Phase 5

## Related Documentation

- [Architecture](../ARCHITECTURE.md) - System design
- [Spec](../specs/core/spec.md) - Technical requirements
- [Plan](../specs/core/plan.md) - Implementation phases
- [ADR 004](../history/adr/004-authentication-better-auth-choice.md) - Authentication decision

## Support

For questions or issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [Architecture](../ARCHITECTURE.md)
3. Check API docs: http://localhost:8000/api/docs

---

**Status**: Phase 0 (Core setup complete) | **Last Updated**: 2025-12-24
