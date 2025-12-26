# System Architecture

**Physical AI & Humanoid Robotics Interactive Textbook**

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Frontend Layer                                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Docusaurus 3 + Custom React Theme (No Defaults)                 │   │
│  │ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │   │
│  │ │   Navbar         │  │   Main Content   │  │   Sidebar        │ │   │
│  │ ├──────────────────┤  ├──────────────────┤  ├──────────────────┤ │   │
│  │ │ Logo & Title     │  │ Chapter Content  │  │ Module Tree      │ │   │
│  │ │ Module Dropdown  │  │ (MDX + React)    │  │ Chapter List     │ │   │
│  │ │ Search Input     │  │ Code Examples    │  │ Progress Bar     │ │   │
│  │ │ Theme Toggle     │  │ Quiz Components  │  │ (Placeholder)    │ │   │
│  │ │ Login Link       │  │ Chatbot Widget   │  │ Collapsible      │ │   │
│  │ └──────────────────┘  └──────────────────┘  └──────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│  Technology: React 18+, TypeScript, Tailwind CSS, Framer Motion          │
│  Colors: Primary Blue (#4A90E2), Accent Green (#7ED321), Neutrals       │
│  Dark Mode: Full support (theme toggle in navbar)                        │
│  Responsive: Mobile-first design (hamburger menu on mobile)              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
         ┌──────────▼──────────┐        ┌──────────▼──────────┐
         │   API Calls (REST)  │        │  WebSocket (Chat)   │
         │  (HTTP over HTTPS)  │        │  (Real-time Q&A)    │
         └──────────┬──────────┘        └──────────┬──────────┘
                    │                               │
└─────────────────────────────────────────────────────────────────────────┐
│                           Backend Layer (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ FastAPI Server (Port 8000, Async)                               │   │
│  │ ┌──────────────────────────────────────────────────────────────┐│   │
│  │ │ Authentication & Authorization                              ││   │
│  │ │ ├─ POST /api/auth/signup  (email, password → JWT token)    ││   │
│  │ │ ├─ POST /api/auth/signin  (email, password → JWT token)    ││   │
│  │ │ ├─ POST /api/auth/logout  (clear token)                    ││   │
│  │ │ └─ GET  /api/auth/me      (current user profile)           ││   │
│  │ ├─ Middleware: JWT token verification, role-based access      ││   │
│  │ └─ Better-Auth: Session management, email verification        ││   │
│  │ ┌──────────────────────────────────────────────────────────────┐│   │
│  │ │ Content & Chatbot APIs                                      ││   │
│  │ │ ├─ GET  /api/chapters       (list all chapters)            ││   │
│  │ │ ├─ GET  /api/chapters/{id}  (chapter content)              ││   │
│  │ │ ├─ POST /api/chat/query     (RAG chatbot question)         ││   │
│  │ │ ├─ GET  /api/chat/history   (user chat history)            ││   │
│  │ │ └─ POST /api/progress       (save learning progress)       ││   │
│  │ │ ┌────────────────────────────────────────────────────────┐││   │
│  │ │ │ RAG Chatbot Pipeline                                   │││   │
│  │ │ │ 1. Embedding (OpenAI text-embedding-3-small)           │││   │
│  │ │ │ 2. Retrieval (Qdrant semantic search, top-5)           │││   │
│  │ │ │ 3. Ranking (relevance filtering, confidence scoring)   │││   │
│  │ │ │ 4. Augmentation (format context for LLM)               │││   │
│  │ │ │ 5. Generation (GPT-4 with system prompt)               │││   │
│  │ │ │ 6. Filtering (validate grounded in source)             │││   │
│  │ │ │ Output: answer + sources + confidence score            │││   │
│  │ │ └────────────────────────────────────────────────────────┘││   │
│  │ ├─ User Profiling & Personalization                           ││   │
│  │ │ ├─ User background detection (software/hardware/goal)      ││   │
│  │ │ ├─ Difficulty level selection (Beginner/Intermediate/Advanced) ││
│  │ │ ├─ Language preference (English/Urdu)                      ││   │
│  │ │ └─ Content adaptation per profile                          ││   │
│  │ └─ Error Handling (JSON error responses with status codes)    ││   │
│  │ └─ Logging (structured JSON logs for monitoring)              ││   │
│  │ └─ Health Check: GET /health, /api/health (DB + Qdrant)      ││   │
│  └──────────────────────────────────────────────────────────────┘│   │
│  Framework: FastAPI, Python 3.10+, Async (asyncio, aiohttp)      │   │
│  CORS: Enabled for frontend domain (localhost:3000)              │   │
│  Rate Limiting: TBD (Phase 4)                                     │   │
│  Caching: Redis caching for frequent queries (Phase 4)            │   │
└─────────────────────────────────────────────────────────────────────────┘
                    │                               │
         ┌──────────▼──────────┐        ┌──────────▼──────────┐
         │  Database Access    │        │  Vector DB Access   │
         │  (SQLAlchemy ORM)   │        │  (Qdrant Client)    │
         └──────────┬──────────┘        └──────────┬──────────┘
                    │                               │
└─────────────────────────────────────────────────────────────────────────┐
│                           Data Layer                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Neon Postgres (Serverless, ACID)                                │   │
│  │ ├─ users (email, password_hash, background, learning_goal)     │   │
│  │ ├─ user_preferences (difficulty, language, notifications)      │   │
│  │ ├─ chat_sessions (user_id, created_at, updated_at)             │   │
│  │ ├─ chat_messages (session_id, role, content, sources)          │   │
│  │ ├─ chapters (title, module, content, metadata)                 │   │
│  │ ├─ user_progress (user_id, chapter_id, status, completed_at)   │   │
│  │ └─ quizzes (chapter_id, questions, correct_answers)            │   │
│  │                                                                  │   │
│  │ Index Strategy:                                                  │   │
│  │ ├─ users(email) - unique, for login                            │   │
│  │ ├─ chat_messages(session_id, created_at) - for history         │   │
│  │ ├─ user_progress(user_id, chapter_id) - for tracking           │   │
│  │ └─ chapters(module, published) - for discovery                 │   │
│  │                                                                  │   │
│  │ Source of Truth: Relational data (users, progress, chat)        │   │
│  │ Consistency Model: Strong (ACID transactions)                   │   │
│  │ Replication: Neon managed                                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Qdrant Vector Database (Semantic Search for RAG)                │   │
│  │ ├─ Collection: "chapters"                                       │   │
│  │ │  ├─ Vector size: 1536 (OpenAI text-embedding-3-small)        │   │
│  │ │  ├─ Distance metric: Cosine similarity                        │   │
│  │ │  ├─ Indexing: HNSW (Hierarchical Navigable Small World)      │   │
│  │ │  └─ Payload: chunk_id, chapter_id, section, text, metadata   │   │
│  │ ├─ Data Flow: Chapter Content → Chunking (300-500 tokens)       │   │
│  │ │              → OpenAI Embeddings → Qdrant Insert              │   │
│  │ └─ Query Flow: User Query → Embedding → Qdrant Search (top-5)   │   │
│  │                → Rank & Filter → Format Context → GPT-4         │   │
│  │                                                                  │   │
│  │ Source of Truth: Derived from chapters in Postgres              │   │
│  │ Consistency Model: Eventual (lag ~5-10 minutes)                 │   │
│  │ Cache: Frequently-asked queries (Phase 4)                       │   │
│  │ Replication: Qdrant Cloud managed                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ External Services                                                │   │
│  │ ├─ OpenAI API (Embeddings + GPT-4)                              │   │
│  │ │  ├─ text-embedding-3-small (1536 dims, cost-effective)        │   │
│  │ │  └─ gpt-4 (high-quality generation)                           │   │
│  │ ├─ SendGrid (Email Service)                                     │   │
│  │ │  └─ Transactional emails: verification, password reset        │   │
│  │ └─ GitHub (Source Control)                                      │   │
│  │    ├─ Repository: source code, docs, artifacts                 │   │
│  │    └─ Pages: frontend deployment (static hosting)               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow: RAG Chatbot

```
User Query (e.g., "How do I set up ROS 2?")
    ↓
[Embedding Service]
  - Convert query to vector (OpenAI text-embedding-3-small)
  - Vector output: 1536 dimensions
    ↓
[Qdrant Retrieval]
  - Semantic search: find top-5 most similar chunks
  - Cosine similarity scoring
  - Returns: chunk_id, chapter_id, text, confidence_score
    ↓
[Ranking & Filtering]
  - Filter low-confidence results (< 0.7 threshold)
  - Re-rank by relevance
  - Collect top-3 to top-5 results
    ↓
[Context Augmentation]
  - Format retrieved chunks into context string
  - Include: "Based on Chapter X Section Y..."
  - Prepare for GPT-4 prompt
    ↓
[GPT-4 Generation]
  - System prompt: "You are an expert tutor in Physical AI & Humanoid Robotics"
  - User message: original question + context
  - Generate response grounded in provided context
    ↓
[Response Filtering]
  - Verify answer references source material
  - Reject if answer goes beyond indexed content
  - Add source citations and confidence score
    ↓
Response: {
  "answer": "Based on Chapter 1.2...",
  "sources": ["Chapter 1.2 ROS 2 Installation"],
  "confidence": 0.85,
  "full_context": [...chunk details...]
}
```

## Database Schema (Postgres)

### users
```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    background_software VARCHAR,  -- "Beginner", "Intermediate", "Advanced"
    background_hardware VARCHAR,  -- "None", "Some", "Extensive"
    learning_goal VARCHAR,         -- "Career", "Hobby", "Academic", "Research"
    preferred_language VARCHAR DEFAULT 'en',  -- 'en' or 'ur'
    difficulty_level VARCHAR DEFAULT 'Intermediate',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    email_verified BOOLEAN DEFAULT FALSE
);
```

### user_preferences
```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR UNIQUE REFERENCES users(id),
    difficulty_level VARCHAR DEFAULT 'Intermediate',
    language VARCHAR DEFAULT 'en',
    theme VARCHAR DEFAULT 'light',  -- 'light' or 'dark'
    notifications_enabled BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT now()
);
```

### chat_sessions
```sql
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    title VARCHAR,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    topic VARCHAR  -- 'ROS 2', 'Gazebo', 'Isaac', 'VLA'
);
```

### chat_messages
```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id),
    role VARCHAR,  -- 'user' or 'assistant'
    content TEXT,
    sources TEXT[],  -- Array of source references
    confidence FLOAT,  -- 0.0 to 1.0
    created_at TIMESTAMP DEFAULT now(),
    INDEX: (session_id, created_at)
);
```

### chapters
```sql
CREATE TABLE chapters (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    module VARCHAR NOT NULL,  -- 'ROS 2', 'Gazebo/Unity', 'Isaac', 'VLA'
    order_num INTEGER,
    content_path VARCHAR,  -- Path to MDX file
    content_hash VARCHAR,  -- Hash for change detection
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    INDEX: (module, published)
);
```

### user_progress
```sql
CREATE TABLE user_progress (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    chapter_id INTEGER REFERENCES chapters(id),
    status VARCHAR DEFAULT 'not_started',  -- 'not_started', 'in_progress', 'completed'
    quiz_score FLOAT,  -- 0.0 to 100.0
    completed_at TIMESTAMP,
    INDEX: (user_id, chapter_id)
);
```

## API Response Format

All API responses follow this format:

### Success Response
```json
{
  "success": true,
  "data": { /* response body */ },
  "meta": {
    "timestamp": "2025-12-24T10:30:00Z",
    "version": "1.0"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "Invalid email or password",
    "details": "Email not found in system"
  },
  "meta": {
    "timestamp": "2025-12-24T10:30:00Z",
    "path": "/api/auth/signin"
  }
}
```

## Security & Compliance

### Authentication
- JWT tokens (HS256 algorithm)
- Token expiry: 30 days
- Secure password hashing: bcrypt (salt rounds: 12)
- Email verification required before login
- Better-Auth handles session management

### Authorization
- Role-based access (user, admin - Phase 4)
- Protected endpoints require valid JWT
- User can only access their own data (user_id in token)

### Data Protection
- HTTPS only (enforced in production)
- Postgres SSL connections
- Sensitive env vars in `.env.local` (not in git)
- API keys rotated regularly

### Privacy
- User data stored in Neon (EU/US region selectable)
- Chat history retained (user can request deletion)
- No third-party tracking (except OpenAI API usage logging)

## Performance & Scaling

### Frontend
- Static site generation (Docusaurus, pre-rendered)
- Deployed on GitHub Pages (CDN distributed)
- Page load time target: <2s (measured by Lighthouse)

### Backend
- FastAPI async processing (handles concurrent requests)
- Database connection pooling (SQLAlchemy)
- Qdrant indexing (HNSW for O(log N) search)
- Caching layer: Redis (Phase 4)

### RAG Chatbot
- Response time target: <5s
- Embedding latency: ~200ms (OpenAI API)
- Retrieval latency: ~300ms (Qdrant)
- LLM generation latency: ~2-3s (GPT-4)

### Scaling Strategy
- Neon Postgres: auto-scaling (serverless)
- Qdrant Cloud: auto-scaling based on queries
- FastAPI: horizontal scaling (replicas behind load balancer)
- Frontend: infinite CDN distribution

## Monitoring & Observability

### Logging
- Structured JSON logs (FastAPI uvicorn)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Logs to: stdout (for aggregation by platform)

### Metrics (Phase 5)
- Request latency (p50, p95, p99)
- Error rates (by endpoint)
- Database query performance
- Qdrant search performance
- OpenAI API usage & cost

### Alerts (Phase 5)
- High error rates (>5%)
- Slow endpoints (>5s)
- Database connection issues
- Qdrant connection issues
- API key quota exceeded

### APM (Phase 4+)
- Consider: Sentry (error tracking), DataDog (metrics)

## Deployment Architecture

### Frontend (GitHub Pages)
```
GitHub Repo
  ↓ (push to main)
GitHub Actions CI
  ↓ (npm build)
docusaurus-site/build/
  ↓
GitHub Pages (cdn.github.io/...)
```

### Backend (Railway or Vercel)
```
GitHub Repo
  ↓ (push to main)
Railway/Vercel Webhook
  ↓ (build)
Docker Container
  ↓ (deploy)
Railway/Vercel Production
  ↓
API: https://api.physical-ai-textbook.app/
```

### Environment-specific Configuration
- **Development** (localhost): .env.local (git-ignored)
- **Staging** (preview): .env.staging (secrets in GitHub)
- **Production** (live): .env.production (secrets in Railway/Vercel)

## Critical Dependencies

| Component | Purpose | Dependency | Fallback |
|-----------|---------|-----------|----------|
| Neon Postgres | Relational data | Critical | Migrate to AWS RDS |
| Qdrant | RAG retrieval | Critical | Migrate to Pinecone |
| OpenAI API | Embeddings + LLM | Critical | Use local embeddings (Ollama) + Claude API |
| SendGrid | Email verification | Important | Use AWS SES |
| GitHub Pages | Frontend hosting | Important | Migrate to Vercel |

## Architecture Review Checkpoints

- **Phase 0 Gate**: Database schema reviewed, API contracts defined
- **Phase 1 Gate**: Frontend + backend integration tested, RAG pipeline operational
- **Phase 2 Gate**: Personalization system tested, performance baseline established
- **Phase 4 Gate**: Caching, scaling, and performance optimizations in place
- **Phase 6 Gate**: Security audit, accessibility audit, performance audit passed

---

See [history/adr/](history/adr/) for detailed decision records.
