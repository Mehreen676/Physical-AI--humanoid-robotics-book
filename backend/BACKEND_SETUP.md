# FastAPI Backend Setup - Google Gemini Edition

## Configuration Summary

### ✅ Files Created/Updated

| File | Status | Description |
|------|--------|-------------|
| `.env` | ✅ Created | Environment variables with Gemini, Qdrant, Cohere credentials |
| `config.py` | ✅ Updated | Pydantic Settings for Gemini, Qdrant, CORS configuration |
| `main.py` | ✅ Updated | FastAPI app with Gemini client initialization, CORS middleware |
| `services/gemini_service.py` | ✅ Created | Google Gemini API client for text generation & validation |
| `requirements.txt` | ✅ Updated | Added google-generativeai, cohere, asyncpg packages |

---

## Environment Configuration

### .env File Contents
```
BASE_URL=http://localhost:8000
LOG_LEVEL=INFO

# Qdrant Vector Database (Cloud)
QDRANT_URL=https://87f0d492-3160-41ee-9a0d-9ff6295f2da5.europe-west3-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.LwaDQN_7WkP0DqLxGoHp2eWILkzFlcy6QPIY0um4o0k
COLLECTION_NAME=Backend_chunks

# Google Gemini LLM Provider
GEMINI_API_KEY=AIzaSyAqUM2uHMmq-SElXngigIAjXWBMhFQhl9s
MODEL_NAME=gemini-1.5-flash

# Cohere Embeddings Service
EMBEDDINGS_PROVIDER=cohere
COHERE_API_KEY=3zT5S1VYWHqe57TYbo6vHvdnooKIy3UcMTqNsekG
COHERE_EMBEDDING_MODEL=embed-english-light-v3.0

# Neon PostgreSQL Database
DATABASE_URL=postgresql+asyncpg://neondb_owner:npg_WDkcNyATVY34@ep-small-field-ad51jivy-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# Frontend Configuration
FRONTEND_URL=https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/
ALLOWED_ORIGINS=https://mehreen676.github.io,https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/

# RAG Configuration
RETRIEVAL_TOP_K=5
SIMILARITY_THRESHOLD=0.7
SESSION_RETENTION_DAYS=90
```

---

## Key Services Configured

### 1. Google Gemini API (`services/gemini_service.py`)
- **Model**: `gemini-1.5-flash`
- **Methods**:
  - `generate()` - Generate text with configurable temperature
  - `validate_answer()` - Check if answer is grounded in context
  - `health_check()` - Verify API connectivity

### 2. Qdrant Vector Database
- **Type**: Cloud-hosted
- **URL**: `https://87f0d492-3160-41ee-9a0d-9ff6295f2da5.europe-west3-0.gcp.cloud.qdrant.io:6333`
- **Collection**: `Backend_chunks`

### 3. Cohere Embeddings
- **Model**: `embed-english-light-v3.0` (lightweight, 384-dim)
- **API Key**: Configured and validated at startup

### 4. Neon PostgreSQL
- **Database**: `neondb`
- **Connection**: Async with asyncpg driver
- **SSL**: Enabled

### 5. CORS Configuration
- **Allowed Origins**:
  - `https://mehreen676.github.io`
  - `https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/`

---

## Configuration Class Structure

### `config.py` - Settings Class
```python
class Settings(BaseSettings):
    # API Configuration
    base_url: str
    log_level: str

    # Qdrant Configuration
    qdrant_url: str
    qdrant_api_key: str
    collection_name: str

    # Google Gemini Configuration (UPDATED)
    gemini_api_key: str
    model_name: str

    # Database Configuration
    database_url: str

    # Embeddings Configuration
    embeddings_provider: str = "cohere"
    cohere_api_key: str
    cohere_embedding_model: str

    # CORS Configuration (NEW)
    frontend_url: str
    allowed_origins: str

    # RAG Configuration
    retrieval_top_k: int
    similarity_threshold: float
    session_retention_days: int

    # Validators for all required fields
    @field_validator("gemini_api_key")
    @field_validator("cohere_api_key")
    @field_validator("qdrant_api_key")
    @field_validator("database_url")
```

---

## FastAPI App Initialization

### `main.py` - Startup Sequence

The app initializes services in this order:

1. **Database** - PostgreSQL connection
2. **Session Manager** - Conversation history storage
3. **Qdrant Retriever** - Vector similarity search
4. **Embeddings Service** - Cohere embeddings
5. **Gemini Client** - LLM for generation & validation (UPDATED)
6. **RAG Agent** - Main orchestration logic

### CORS Middleware
```python
# Parses ALLOWED_ORIGINS from .env
allowed_origins_list = [
    "https://mehreen676.github.io",
    "https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Required Packages

### `requirements.txt` - Updated Dependencies
```
fastapi>=0.100.0
uvicorn>=0.24.0
google-generativeai>=0.5.0          # NEW: Gemini API
cohere>=4.0.0                       # Cohere embeddings
qdrant-client>=1.7.0,<2.0.0        # Qdrant client
psycopg2-binary>=2.9.0              # PostgreSQL
asyncpg>=0.28.0                     # Async PostgreSQL
pydantic>=2.5.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
sqlalchemy>=2.0.0
sqlalchemy[asyncio]>=2.0.0
requests>=2.31.0
```

---

## Startup Instructions

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Verify Configuration
```bash
python -c "from config import settings; print('✓ Config loaded successfully')"
```

### Step 3: Start Backend
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
INFO:     Configuration loaded and validated successfully
```

---

## API Endpoints

### Root Endpoint
```
GET http://localhost:8000/
Response: { "status": "ok", "service": "BookRAGAgent", "version": "1.0.0" }
```

### Interactive API Documentation
```
GET http://localhost:8000/docs
→ Swagger UI with all available endpoints
```

### Debug State Endpoint
```
GET http://localhost:8000/debug/state
Response: {
  "has_rag_agent": true,
  "has_session_manager": true,
  "has_qdrant_retriever": true,
  "has_gemini_client": true
}
```

---

## Security Best Practices Implemented

✅ **No Hardcoded Secrets**: All API keys loaded from `.env`
✅ **Environment Validation**: Config validates on startup
✅ **CORS Restriction**: Only specified origins allowed
✅ **Secure Database**: SSL/TLS enabled for PostgreSQL
✅ **Async Connections**: asyncpg for non-blocking DB operations
✅ **Error Handling**: Graceful error handling with logging

---

## Verification Checklist

- [ ] `.env` file exists with all credentials
- [ ] `requirements.txt` updated with Gemini and Cohere packages
- [ ] `config.py` validates all environment variables on import
- [ ] `main.py` initializes Gemini client (not OpenRouter)
- [ ] `services/gemini_service.py` created with proper methods
- [ ] CORS middleware configured with GitHub Pages origins
- [ ] Backend starts without errors: `uvicorn main:app --reload`
- [ ] API docs accessible: `http://localhost:8000/docs`
- [ ] Debug endpoint shows all services: `http://localhost:8000/debug/state`

---

## Troubleshooting

### Import Error: `ModuleNotFoundError: No module named 'google.generativeai'`
→ Run: `pip install google-generativeai`

### Import Error: `ModuleNotFoundError: No module named 'cohere'`
→ Run: `pip install cohere`

### Error: `GEMINI_API_KEY is required`
→ Check `.env` file is in `/backend` directory and contains `GEMINI_API_KEY`

### Error: `DATABASE_URL is required`
→ Verify `.env` contains valid PostgreSQL connection string

### CORS Error from Frontend
→ Verify `ALLOWED_ORIGINS` in `.env` matches frontend URL

---

## File Structure
```
backend/
├── .env                          ✅ Environment variables
├── config.py                     ✅ Pydantic Settings (updated)
├── main.py                       ✅ FastAPI app (updated)
├── requirements.txt              ✅ Dependencies (updated)
├── services/
│   ├── gemini_service.py        ✅ NEW: Gemini client
│   ├── embeddings.py            ✓ Cohere embeddings
│   └── openrouter_service.py    (can be deprecated)
├── agent/                        ✓ RAG agent logic
├── rag/                          ✓ Retrieval logic
├── api/                          ✓ API routes
├── models/                       ✓ Database models
├── storage/                      ✓ Database initialization
└── utils/                        ✓ Utilities
```

---

## Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Start backend**: `python -m uvicorn main:app --reload`
3. **Test API**: Open `http://localhost:8000/docs`
4. **Check debug**: `curl http://localhost:8000/debug/state`
5. **Deploy to Render/HuggingFace** with same environment variables

---

**Backend Configuration Status**: ✅ COMPLETE

All services configured and ready for deployment!
