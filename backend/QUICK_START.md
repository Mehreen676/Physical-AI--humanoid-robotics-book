# Backend Quick Start Guide

## What's Been Configured

### ✅ Files Created/Updated

```
backend/
├── .env                          ✅ NEW: Your environment variables
│   ├── QDRANT_URL (cloud)
│   ├── GEMINI_API_KEY
│   ├── COHERE_API_KEY
│   ├── DATABASE_URL
│   └── CORS origins
│
├── config.py                     ✅ UPDATED: Now supports Gemini
│   ├── Replaced OpenRouter with Gemini
│   ├── Added Cohere API key validation
│   └── Added CORS configuration
│
├── main.py                       ✅ UPDATED: Gemini integration
│   ├── CORS middleware with allowed origins
│   ├── Gemini client initialization (Step 5)
│   └── RAG agent using Gemini
│
├── services/
│   ├── gemini_service.py        ✅ NEW: Gemini API client
│   │   ├── generate() - Text generation
│   │   ├── validate_answer() - Grounding validation
│   │   └── health_check() - API status
│   ├── embeddings.py            ✓ Cohere embeddings
│   └── openrouter_service.py    (legacy - can remove)
│
└── requirements.txt              ✅ UPDATED: New packages added
    ├── google-generativeai>=0.5.0
    ├── cohere>=4.0.0
    └── asyncpg>=0.28.0
```

---

## Running the Backend

### Step 1: Install Dependencies (First Time Only)
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Start the Backend
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Test the Backend (New Terminal)
```bash
# Test root endpoint
curl http://localhost:8000/

# View API documentation
open http://localhost:8000/docs

# Check service status
curl http://localhost:8000/debug/state
```

---

## What Each Service Does

| Service | Purpose | Status |
|---------|---------|--------|
| **Gemini** | Generate answers from context | ✅ Configured |
| **Qdrant** | Store and search document embeddings | ✅ Configured |
| **Cohere** | Generate embeddings for documents | ✅ Configured |
| **PostgreSQL** | Store conversation sessions | ✅ Configured |
| **CORS** | Allow frontend requests | ✅ Configured |

---

## Environment Variables Loaded

Your `.env` file contains:

```
✓ QDRANT_URL = https://87f0d492-3160-41ee-9a0d-9ff6295f2da5.europe-west3-0.gcp.cloud.qdrant.io:6333
✓ GEMINI_API_KEY = AIzaSyAqUM2uHMmq-SElXngigIAjXWBMhFQhl9s
✓ COHERE_API_KEY = 3zT5S1VYWHqe57TYbo6vHvdnooKIy3UcMTqNsekG
✓ DATABASE_URL = postgresql+asyncpg://neondb_owner:...
✓ ALLOWED_ORIGINS = https://mehreen676.github.io,...
```

All loaded at startup and validated before app starts.

---

## API Documentation

Once running, open: **http://localhost:8000/docs**

You'll see all available endpoints:
- `GET /` - Root endpoint
- `GET /debug/state` - Service status
- `POST /chat` - Chat with RAG agent (typical endpoint)
- Other RAG endpoints...

---

## Key Changes from Previous Setup

| Item | Before | After |
|------|--------|-------|
| **LLM** | OpenRouter | ✅ Google Gemini |
| **Qdrant** | Local Docker | ✅ Cloud Qdrant |
| **Database** | PostgreSQL | ✅ PostgreSQL (asyncpg) |
| **Embeddings** | Cohere | ✅ Cohere |
| **CORS** | Allow all (*) | ✅ GitHub Pages only |

---

## Debug: Check What's Initialized

```bash
curl http://localhost:8000/debug/state
```

Response:
```json
{
  "has_rag_agent": true,
  "has_session_manager": true,
  "has_qdrant_retriever": true,
  "has_gemini_client": true
}
```

All should be `true` if startup was successful.

---

## Logs to Expect on Startup

```
Configuration loaded and validated successfully
Step 1: Initializing database...
Step 2: Initializing session manager...
Step 3: Initializing Qdrant retriever...
Step 4: Initializing embeddings service...
Step 5: Initializing Gemini client...
Step 6: Initializing RAG agent...
Dependencies injected into app.state
Application startup complete
```

---

## Deployment

To deploy to Render or HuggingFace, set the same environment variables:

```
QDRANT_URL=https://87f0d492-3160-41ee-9a0d-9ff6295f2da5.europe-west3-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
GEMINI_API_KEY=AIzaSyAqUM2uHMmq-SElXngigIAjXWBMhFQhl9s
COHERE_API_KEY=3zT5S1VYWHqe57TYbo6vHvdnooKIy3UcMTqNsekG
DATABASE_URL=postgresql+asyncpg://neondb_owner:...
ALLOWED_ORIGINS=https://mehreen676.github.io,https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: google.generativeai` | `pip install google-generativeai` |
| `GEMINI_API_KEY is required` | Check `.env` exists in `/backend` directory |
| `CORS error from frontend` | Verify `ALLOWED_ORIGINS` includes your frontend URL |
| `Connection refused to Qdrant` | Check QDRANT_URL is correct cloud endpoint |

---

## Next: Run and Test

```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn main:app --reload

# Terminal 2: Test endpoint (after backend starts)
curl http://localhost:8000/docs
```

That's it! Your FastAPI backend is now configured with Google Gemini. 🚀
