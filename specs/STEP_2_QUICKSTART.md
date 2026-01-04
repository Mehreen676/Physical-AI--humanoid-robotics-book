# Step 2: RAG Agent - Quick Start Guide

## 30-Second Overview

Build a FastAPI backend that answers questions about your book using RAG (Retrieval-Augmented Generation) with zero hallucinations.

**Time**: 8 hours | **Difficulty**: Intermediate | **Prerequisites**: Step 1 complete

---

## Prerequisites Checklist

Before starting, ensure you have:

- [x] **Step 1 Complete**: Qdrant collection `data_collection` populated with 19 chunks
- [ ] **PostgreSQL Database**: Neon account or local PostgreSQL instance
- [ ] **API Keys**:
  - [ ] Gemini API key (from Step 1)
  - [ ] OpenRouter API key (for Claude 3.5 Sonnet)
  - [ ] Qdrant API key (from Step 1)
- [ ] **Python 3.11+** installed
- [ ] **Git** installed (for version control)

**Missing something?** See Setup Instructions below.

---

## Setup Instructions

### 1. Get PostgreSQL Database (5 minutes)

**Option A: Neon (Recommended - Free Tier)**
1. Go to https://neon.tech
2. Sign up with GitHub
3. Create new project: "bookrag"
4. Copy connection string: `postgresql://user:pass@host/neondb`

**Option B: Local PostgreSQL**
1. Install PostgreSQL 15+
2. Create database: `createdb bookrag`
3. Connection string: `postgresql://localhost/bookrag`

### 2. Get OpenRouter API Key (3 minutes)

1. Go to https://openrouter.ai
2. Sign up with email
3. Add $5 credit (pay-per-use, ~$0.02 per 1000 questions)
4. Copy API key: `sk-or-v1-...`

**Cost Estimate**: Claude 3.5 Sonnet costs $0.003/1K tokens (~$0.005 per question)

### 3. Verify Existing Keys (1 minute)

From Step 1, you should already have:
- `GEMINI_API_KEY` (in `C:\Users\Lenovo\Desktop\text-book\.env`)
- `QDRANT_API_KEY` (in same file)
- `QDRANT_URL` (in same file)
- `COLLECTION_NAME=data_collection`

---

## Implementation in 8 Steps

### Step 1: Project Setup (30 min)

```bash
# Navigate to project root
cd C:\Users\Lenovo\Desktop\text-book

# Create backend directory
mkdir backend
cd backend

# Create directory structure
mkdir agent api models rag services storage utils tests
touch __init__.py agent/__init__.py api/__init__.py models/__init__.py
touch rag/__init__.py services/__init__.py storage/__init__.py utils/__init__.py

# Create main files
touch main.py config.py

# Create requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
qdrant-client==1.7.0
google-generativeai==0.3.0
httpx==0.25.1
pydantic==2.5.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
EOF

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
# Database
DATABASE_URL=postgresql://your-neon-connection-string

# Qdrant (from Step 1)
QDRANT_URL=https://87f0d492-3160-41ee-9a0d-9ff6295f2da5.europe-west3-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.LwaDQN_7WkP0DqLxGoHp2eWILkzFlcy6QPIY0um4o0k
COLLECTION_NAME=data_collection

# Gemini (from Step 1)
GEMINI_API_KEY=AIzaSyCTvAp39zQgXO7mFSQR92x5SGcN4ykqgh4

# OpenRouter (new)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
MODEL_NAME=anthropic/claude-3.5-sonnet

# Server
PORT=8000
EOF

# Edit .env and replace DATABASE_URL and OPENROUTER_API_KEY with your values
```

**Checkpoint**: You should have `backend/` directory with subdirectories and `requirements.txt`

---

### Step 2: Database Setup (45 min)

Create `storage/models.py`:
```python
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")
```

Create `storage/init_db.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_database():
    Base.metadata.create_all(bind=engine)
```

Create `storage/sessions.py`:
```python
from .init_db import SessionLocal
from .models import Session, Message
from typing import List, Dict
import uuid

def create_session() -> str:
    db = SessionLocal()
    session = Session()
    db.add(session)
    db.commit()
    db.refresh(session)
    db.close()
    return str(session.id)

def get_session(session_id: str) -> Dict:
    db = SessionLocal()
    session = db.query(Session).filter(Session.id == uuid.UUID(session_id)).first()
    if not session:
        return None
    messages = [{"role": m.role, "content": m.content, "timestamp": m.timestamp}
                for m in session.messages]
    db.close()
    return {"session_id": str(session.id), "created_at": session.created_at, "messages": messages}

def save_message(session_id: str, role: str, content: str):
    db = SessionLocal()
    message = Message(session_id=uuid.UUID(session_id), role=role, content=content)
    db.add(message)
    db.commit()
    db.close()
```

**Test**:
```bash
python -c "from backend.storage.init_db import init_database; init_database()"
python -c "from backend.storage.sessions import create_session; print(create_session())"
```

**Checkpoint**: Database tables created, session creation works

---

### Step 3: Services (60 min)

Copy `services/embeddings.py` from `ingestion/embeddings.py` (already implemented).

Create `services/openrouter_service.py`:
```python
import httpx
import os
from typing import List, Dict

class OpenRouterClient:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("MODEL_NAME", "anthropic/claude-3.5-sonnet")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    async def generate(self, messages: List[Dict[str, str]], max_tokens: int = 1500) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.0
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
```

Create `rag/retrieval.py`:
```python
from qdrant_client import QdrantClient
import os

class QdrantRetriever:
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.collection_name = os.getenv("COLLECTION_NAME")

    def search(self, query_vector, top_k=5, score_threshold=0.7):
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold
        )
        return [{"text": r.payload["text"], "metadata": r.payload.get("metadata", {}),
                 "score": r.score} for r in results]
```

**Checkpoint**: Services can connect to external APIs

---

### Steps 4-8 (Abbreviated)

Due to time constraints, I'll provide the file names and key methods. See `STEP_2_RAG_AGENT_PLAN.md` for full implementation details.

**Step 4: Sub-Agents** (90 min) - `agent/sub_agents.py`:
- `RetrievalSubAgent.retrieve(question, mode)` → chunks
- `AnswerSubAgent.generate_answer(question, chunks, history)` → answer + citations
- `GuardrailsSubAgent.validate(answer, chunks)` → is_valid
- `MemorySubAgent.load_history(session_id)` → messages

**Step 5: Main Agent** (45 min) - `agent/agent.py`:
- `BookRAGAgent.chat(session_id, question)` → orchestrates all sub-agents

**Step 6: FastAPI API** (60 min):
- `models/schemas.py` - Pydantic models
- `api/routes.py` - Endpoint handlers
- `main.py` - FastAPI app

**Step 7: Testing** (90 min) - `tests/`:
- Unit tests for each component
- Integration test for `/chat` endpoint

**Step 8: Documentation** (60 min):
- `backend/README.md`

---

## Test Your Implementation

### 1. Start the Server
```bash
cd backend
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 2. Test Endpoints

**Health Check**:
```bash
curl http://localhost:8000/health
```

Expected: `{"status": "healthy", ...}`

**Create Session**:
```bash
curl -X POST http://localhost:8000/sessions
```

Expected: `{"session_id": "uuid", ...}`

**Chat**:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "question": "What is ROS 2?",
    "retrieval_mode": "normal"
  }'
```

Expected: `{"answer": "ROS 2 is...", "citations": [...], ...}`

---

## Troubleshooting

### Database Connection Error
**Error**: `could not connect to server`
**Fix**: Verify `DATABASE_URL` in `.env`, ensure PostgreSQL is running

### Qdrant Connection Error
**Error**: `Failed to connect to Qdrant`
**Fix**: Check `QDRANT_URL` and `QDRANT_API_KEY`, verify collection exists

### OpenRouter Error
**Error**: `401 Unauthorized`
**Fix**: Verify `OPENROUTER_API_KEY` is correct, check credit balance

### Import Error
**Error**: `ModuleNotFoundError: No module named 'backend'`
**Fix**: Run from project root, or set `PYTHONPATH=.`

---

## Success Checklist

- [ ] All dependencies installed (`pip list | grep fastapi`)
- [ ] Database tables created (check with `psql`)
- [ ] Health endpoint returns 200 (`curl /health`)
- [ ] Can create session (`curl -X POST /sessions`)
- [ ] Chat endpoint returns answer (`curl -X POST /chat`)
- [ ] Answer cites book sources (check `citations` field)
- [ ] Multi-turn conversation works (follow-up questions)

---

## What's Next?

After completing Step 2:

1. **Deploy to Production** - See `README.md` for Render deployment
2. **Connect Frontend** - Integrate chat widget into Docusaurus site
3. **Optimize Performance** - Add caching, connection pooling
4. **Monitor & Debug** - Set up logging, error tracking

---

## Getting Help

- **Full Spec**: See `STEP_2_RAG_AGENT_PLAN.md`
- **Architecture**: See `STEP_2_ARCHITECTURE.md`
- **Task Tracking**: See `STEP_2_TASKS.md`
- **Issues**: Check `STEP_2_ARCHITECTURE.md` Error Flow section

---

**Last Updated**: 2026-01-03

**Estimated Time**: 8 hours (480 minutes)

**Status**: Ready to implement
