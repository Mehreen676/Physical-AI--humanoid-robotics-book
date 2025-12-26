# PHASE 0 TASK BRIEF - @BackendEngineer

**Project**: Physical AI & Humanoid Robotics Interactive Textbook
**Phase**: 0 (Foundation & Setup)
**Duration**: 3-4 days (parallel execution)
**Owner**: @BackendEngineer
**Status**: READY FOR EXECUTION

---

## Overview

You are responsible for setting up the backend infrastructure: databases (Neon Postgres + Qdrant), FastAPI server, and authentication. These are **critical path** items—everything else depends on completion.

---

## BLOCK 1: Database Setup (Day 1)

### Task 0.2.1: Create Neon Postgres Database

**Objective**: Provision managed PostgreSQL database with schema.

**Steps**:

1. **Create Neon Account** (if not already done)
   - Go to https://neon.tech/
   - Sign up (free tier available)
   - Create project: `physical-ai-textbook`

2. **Create Database**
   - Default database `neondb` created automatically
   - Get connection string (format: `postgresql://user:password@host/dbname`)
   - Copy to clipboard

3. **Verify Connection**
   ```bash
   # Using psql (if installed)
   psql "your_neon_connection_string"
   # Should connect successfully

   # Or test in Python
   pip install psycopg2-binary
   python -c "import psycopg2; conn = psycopg2.connect('your_connection_string'); print('Connected!')"
   ```

4. **Save Connection String**
   - Create `.env.local` in project root (NOT in git)
   - Add: `DATABASE_URL=postgresql://...`
   - Verify in `.gitignore`: `.env.local` is excluded

**Acceptance Criteria**:
- [ ] Neon account created
- [ ] Database `neondb` exists
- [ ] Connection string obtained
- [ ] Local connection test succeeds (psql or Python)
- [ ] `.env.local` created with `DATABASE_URL`

**Estimated Time**: 30 minutes

---

### Task 0.2.2: Design & Create Database Schema

**Objective**: Create tables for users, chat, chapters, progress, preferences.

**Steps**:

1. **Create SQLAlchemy Models**
   - Create `backend/fastapi-app/models.py` (or `models/` directory)
   - Define ORM models:

```python
# backend/fastapi-app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    background_software = Column(String)  # beginner|intermediate|advanced
    background_hardware = Column(String)  # none|basic|extensive
    learning_goal = Column(String)  # fundamentals|specialization|research
    created_at = Column(DateTime, default=datetime.utcnow)

    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    chat_sessions = relationship("ChatSession", back_populates="user")
    progress = relationship("UserProgress", back_populates="user")

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    dark_mode = Column(Boolean, default=True)
    preferred_language = Column(String, default='en')  # en|ur
    show_advanced = Column(Boolean, default=False)
    auto_translate = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user|assistant
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    feedback = Column(Integer)  # -1|0|1 (bad|neutral|good)

    session = relationship("ChatSession", back_populates="messages")

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(String, primary_key=True)  # module-X-chapter-Y format
    module = Column(Integer, nullable=False, index=True)
    chapter = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    content_type = Column(String)  # theory|code|quiz

    progress = relationship("UserProgress", back_populates="chapter")

class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=False, index=True)
    completion_pct = Column(Integer, default=0)
    quiz_score = Column(Integer)
    time_spent_sec = Column(Integer, default=0)
    bookmarked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="progress")
    chapter = relationship("Chapter", back_populates="progress")
```

2. **Test Model Creation**
   ```bash
   cd backend/fastapi-app
   python -c "
   from sqlalchemy import create_engine
   import os
   from models import Base

   DATABASE_URL = os.getenv('DATABASE_URL')
   engine = create_engine(DATABASE_URL)
   Base.metadata.create_all(bind=engine)
   print('✓ Tables created successfully')
   "
   ```

3. **Verify Tables Exist**
   ```bash
   psql "your_neon_connection_string" -c "\dt"
   # Should show: users, user_preferences, chat_sessions, chat_messages, chapters, user_progress
   ```

**Acceptance Criteria**:
- [ ] SQLAlchemy models defined in `backend/fastapi-app/models.py`
- [ ] All relationships configured correctly
- [ ] Tables created in Neon database
- [ ] `\dt` shows all 6 tables
- [ ] Foreign keys and indexes created

**Estimated Time**: 1 hour

---

### Task 0.2.3: Initialize Qdrant Vector Database

**Objective**: Set up vector database for RAG embeddings.

**Steps**:

1. **Choose Deployment**
   - **Option A (Recommended for hackathon)**: Qdrant Cloud
     - Go to https://qdrant.io/
     - Sign up for free tier
     - Create cluster: `chapters-db`
   - **Option B (Local dev)**: Docker
     ```bash
     docker run -p 6333:6333 qdrant/qdrant:latest
     ```

2. **Create Collection**
   ```bash
   # Via curl (replace API_KEY and HOST)
   curl -X PUT "https://your-qdrant-host/collections/chapters" \
     -H "api-key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
       "vectors": {
         "size": 1536,
         "distance": "Cosine"
       },
       "payload_schema": {
         "properties": {
           "module": {"type": "integer"},
           "chapter": {"type": "integer"},
           "section": {"type": "string"},
           "content_type": {"type": "string"}
         }
       }
     }'
   ```

3. **Verify Collection**
   ```bash
   curl -X GET "https://your-qdrant-host/collections/chapters" \
     -H "api-key: your-api-key"
   # Should return collection info
   ```

4. **Save Credentials**
   - Add to `.env.local`:
     ```
     QDRANT_URL=https://your-qdrant-host
     QDRANT_API_KEY=your-api-key
     ```

**Acceptance Criteria**:
- [ ] Qdrant account/instance created
- [ ] Collection "chapters" exists
- [ ] Vector size: 1536, distance: Cosine
- [ ] Curl GET request returns collection info
- [ ] Credentials in `.env.local`

**Estimated Time**: 30 minutes

---

### Task 0.2.4: Connect Databases in FastAPI

**Objective**: Set up SQLAlchemy + Qdrant clients.

**Steps**:

1. **Create Database Client**
   ```python
   # backend/fastapi-app/database.py
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   import os

   DATABASE_URL = os.getenv("DATABASE_URL")
   engine = create_engine(
       DATABASE_URL,
       pool_size=5,
       max_overflow=10,
       echo=False  # Set to True for debugging
   )

   SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

   def get_db():
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()
   ```

2. **Create Qdrant Client**
   ```python
   # backend/fastapi-app/qdrant_client.py
   from qdrant_client import QdrantClient
   import os

   QDRANT_URL = os.getenv("QDRANT_URL")
   QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

   qdrant = QdrantClient(
       url=QDRANT_URL,
       api_key=QDRANT_API_KEY
   )

   def test_connection():
       try:
           collections = qdrant.get_collections()
           return {"status": "ok", "collections": len(collections.collections)}
       except Exception as e:
           return {"status": "error", "message": str(e)}
   ```

3. **Test Connections**
   ```bash
   cd backend/fastapi-app
   python -c "
   from database import SessionLocal
   from qdrant_client_helper import test_connection

   # Test Postgres
   db = SessionLocal()
   result = db.execute('SELECT 1')
   print('✓ Postgres connected')
   db.close()

   # Test Qdrant
   status = test_connection()
   print(f'✓ Qdrant: {status}')
   "
   ```

**Acceptance Criteria**:
- [ ] `database.py` created with SQLAlchemy engine
- [ ] `qdrant_client.py` created with Qdrant client
- [ ] Dependency injection setup (`get_db()`)
- [ ] Both connections test successfully
- [ ] No errors in connection logs

**Estimated Time**: 1 hour

---

## BLOCK 2: FastAPI Backend Skeleton (Day 2)

### Task 0.4.1: Create FastAPI App with Error Handling

**Objective**: Initialize FastAPI with logging, middleware, CORS.

**Steps**:

1. **Create `backend/fastapi-app/main.py`**
   ```python
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   import logging
   import json
   from datetime import datetime

   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
   )
   logger = logging.getLogger(__name__)

   # Create app
   app = FastAPI(
       title="Physical AI Textbook API",
       description="RAG Chatbot + Course Management",
       version="1.0.0"
   )

   # CORS configuration
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "http://localhost:3000",  # Local dev
           "https://yourgithubusername.github.io",  # GitHub Pages
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

   # Health check endpoint
   @app.get("/health")
   def health():
       return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

   @app.get("/api/health")
   def api_health():
       from database import SessionLocal
       from qdrant_client_helper import test_connection

       try:
           db = SessionLocal()
           db.execute('SELECT 1')
           db.close()
           postgres_ok = True
       except:
           postgres_ok = False

       qdrant_status = test_connection()
       qdrant_ok = qdrant_status.get("status") == "ok"

       return {
           "status": "ok" if (postgres_ok and qdrant_ok) else "partial",
           "postgres": postgres_ok,
           "qdrant": qdrant_ok
       }

   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
   ```

2. **Install Dependencies**
   ```bash
   cd backend/fastapi-app
   pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv qdrant-client pydantic
   pip freeze > requirements.txt
   ```

3. **Create `.env.local` (if not already done)**
   ```
   DATABASE_URL=postgresql://...
   QDRANT_URL=https://...
   QDRANT_API_KEY=...
   ```

4. **Run Server**
   ```bash
   cd backend/fastapi-app
   uvicorn main:app --reload
   # Should start on http://localhost:8000
   # Test: curl http://localhost:8000/health → should return {"status": "ok", ...}
   ```

**Acceptance Criteria**:
- [ ] FastAPI app starts without errors
- [ ] `GET /health` returns 200 with `{"status": "ok"}`
- [ ] `GET /api/health` returns database status
- [ ] CORS configured for localhost:3000
- [ ] Logging shows requests in JSON format
- [ ] `requirements.txt` created with all dependencies

**Estimated Time**: 1 hour

---

### Task 0.4.2: Create Pydantic Models

**Objective**: Define request/response models for API validation.

**Steps**:

1. **Create `backend/fastapi-app/schemas.py`**
   ```python
   from pydantic import BaseModel, EmailStr
   from typing import Optional
   from datetime import datetime

   # Auth schemas
   class SignupRequest(BaseModel):
       email: EmailStr
       password: str

   class SigninRequest(BaseModel):
       email: EmailStr
       password: str

   class TokenResponse(BaseModel):
       access_token: str
       token_type: str = "bearer"
       user_id: str

   # User schemas
   class UserProfile(BaseModel):
       id: str
       email: str
       background_software: Optional[str]
       background_hardware: Optional[str]
       learning_goal: Optional[str]
       created_at: datetime

   class UserPreferencesUpdate(BaseModel):
       dark_mode: Optional[bool]
       preferred_language: Optional[str]
       show_advanced: Optional[bool]
       auto_translate: Optional[bool]

   # Chat schemas
   class ChatQuery(BaseModel):
       message: str
       selected_text: Optional[str]
       user_id: Optional[str]
       context: Optional[dict]

   class ChatResponse(BaseModel):
       response: str
       sources: list
       confidence: float
       session_id: str

   class ChatMessage(BaseModel):
       id: str
       role: str
       content: str
       timestamp: datetime

   # Content schemas
   class ChapterMetadata(BaseModel):
       id: str
       module: int
       chapter: int
       title: str
       content_type: str

   class ChapterContent(BaseModel):
       id: str
       title: str
       content: str
       metadata: ChapterMetadata

   # Progress schemas
   class ProgressUpdate(BaseModel):
       completion_pct: Optional[int]
       quiz_score: Optional[int]
       bookmarked: Optional[bool]

   class ProgressResponse(BaseModel):
       chapter_id: str
       completion_pct: int
       quiz_score: Optional[int]
       time_spent_sec: int
       bookmarked: bool
   ```

**Acceptance Criteria**:
- [ ] All schemas defined in `schemas.py`
- [ ] Field validation configured (required, email, etc.)
- [ ] Type hints complete
- [ ] Schema tests pass (Pydantic validates correctly)

**Estimated Time**: 45 minutes

---

### Task 0.4.3: Set Up Authentication Middleware

**Objective**: Implement JWT token validation for protected routes.

**Steps**:

1. **Create `backend/fastapi-app/auth.py`**
   ```python
   from fastapi import Depends, HTTPException, status
   from fastapi.security import HTTPBearer, HTTPAuthCredentials
   import jwt
   import os
   from datetime import datetime, timedelta

   SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
   ALGORITHM = "HS256"
   ACCESS_TOKEN_EXPIRE_DAYS = 30

   security = HTTPBearer()

   def create_access_token(data: dict):
       to_encode = data.copy()
       expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
       to_encode.update({"exp": expire})
       encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
       return encoded_jwt

   def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
       token = credentials.credentials
       try:
           payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
           user_id: str = payload.get("sub")
           if user_id is None:
               raise HTTPException(status_code=401, detail="Invalid token")
           return user_id
       except jwt.ExpiredSignatureError:
           raise HTTPException(status_code=401, detail="Token expired")
       except jwt.InvalidTokenError:
           raise HTTPException(status_code=401, detail="Invalid token")

   def get_current_user(user_id: str = Depends(verify_token)):
       return user_id
   ```

2. **Update `main.py`** (add import):
   ```python
   from auth import get_current_user

   # Example protected route
   @app.get("/api/user/profile")
   def get_profile(user_id: str = Depends(get_current_user)):
       return {"user_id": user_id, "message": "Protected route working"}
   ```

**Acceptance Criteria**:
- [ ] JWT creation function works
- [ ] Token verification checks expiry and signature
- [ ] Protected routes return 401 if no token
- [ ] Protected routes return user_id if valid token
- [ ] Dependency injection setup correctly

**Estimated Time**: 45 minutes

---

### Task 0.4.4: Create Basic API Endpoints

**Objective**: Implement placeholder endpoints for testing.

**Steps**:

1. **Create `backend/fastapi-app/api/health.py`**
   ```python
   from fastapi import APIRouter

   router = APIRouter(prefix="/api", tags=["health"])

   @router.get("/health")
   def health_check():
       return {
           "status": "ok",
           "service": "textbook-api",
           "version": "1.0.0"
       }
   ```

2. **Update `main.py`** to include router:
   ```python
   from api.health import router as health_router

   app.include_router(health_router)
   ```

3. **Test**
   ```bash
   curl http://localhost:8000/api/health
   # Should return 200 with service info
   ```

**Acceptance Criteria**:
- [ ] Health endpoint returns 200
- [ ] Response contains service info
- [ ] Endpoint accessible at `/api/health`

**Estimated Time**: 30 minutes

---

## BLOCK 3: Better-Auth Setup (Day 2-3)

### Task 0.5.1: Initialize Better-Auth

**Objective**: Configure Better-Auth for signup/signin.

**Steps**:

1. **Install Better-Auth**
   ```bash
   cd backend/fastapi-app
   pip install better-auth
   pip freeze > requirements.txt
   ```

2. **Create `backend/fastapi-app/better_auth_config.py`**
   ```python
   from better_auth import BetterAuth
   from database import SessionLocal
   from models import User
   import os

   better_auth = BetterAuth(
       database_url=os.getenv("DATABASE_URL"),
       secret_key=os.getenv("JWT_SECRET", "change-in-production"),
       jwt_algorithm="HS256",
       jwt_expiry_days=30,
       email_provider="sendgrid",  # or "smtp"
       email_from="noreply@textbook.local"
   )
   ```

3. **Configure Email Provider**
   - SendGrid (recommended):
     ```bash
     pip install sendgrid
     # Add to .env.local:
     SENDGRID_API_KEY=your-sendgrid-key
     ```
   - Or local SMTP (for testing)

**Acceptance Criteria**:
- [ ] Better-Auth installed
- [ ] Config created with secret key
- [ ] Email provider configured
- [ ] No import errors

**Estimated Time**: 30 minutes

---

### Task 0.5.2: Create Signup/Signin Endpoints

**Objective**: Implement authentication endpoints.

**Steps**:

1. **Create `backend/fastapi-app/api/auth.py`**
   ```python
   from fastapi import APIRouter, HTTPException
   from schemas import SignupRequest, SigninRequest, TokenResponse
   from better_auth_config import better_auth
   from models import User
   from database import SessionLocal

   router = APIRouter(prefix="/api/auth", tags=["auth"])

   @router.post("/signup", response_model=TokenResponse)
   async def signup(request: SignupRequest):
       db = SessionLocal()
       try:
           # Check if user exists
           existing_user = db.query(User).filter(User.email == request.email).first()
           if existing_user:
               raise HTTPException(status_code=400, detail="Email already registered")

           # Create user via Better-Auth
           token = better_auth.signup(
               email=request.email,
               password=request.password
           )

           # Send verification email
           better_auth.send_verification_email(request.email)

           return {
               "access_token": token,
               "token_type": "bearer",
               "user_id": token.get("user_id")
           }
       finally:
           db.close()

   @router.post("/signin", response_model=TokenResponse)
   async def signin(request: SigninRequest):
       db = SessionLocal()
       try:
           user = db.query(User).filter(User.email == request.email).first()
           if not user:
               raise HTTPException(status_code=401, detail="Invalid credentials")

           # Verify password via Better-Auth
           token = better_auth.signin(
               email=request.email,
               password=request.password
           )

           return {
               "access_token": token,
               "token_type": "bearer",
               "user_id": user.id
           }
       finally:
           db.close()

   @router.post("/logout")
   async def logout(user_id: str):
       # Clear session (optional, JWT is stateless)
       return {"status": "logged_out"}
   ```

2. **Include router in `main.py`**:
   ```python
   from api.auth import router as auth_router
   app.include_router(auth_router)
   ```

3. **Test**
   ```bash
   # Signup
   curl -X POST http://localhost:8000/api/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "secure123"}'

   # Signin
   curl -X POST http://localhost:8000/api/auth/signin \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "secure123"}'
   ```

**Acceptance Criteria**:
- [ ] POST /api/auth/signup creates user, returns token
- [ ] POST /api/auth/signin validates credentials, returns token
- [ ] Email verification sent (check email)
- [ ] Tokens valid (decode shows user_id)
- [ ] Invalid credentials return 401

**Estimated Time**: 1.5 hours

---

### Task 0.5.3: Create Logout & Session Management

**Objective**: Implement logout and token expiry.

**Steps**:

1. **Update `api/auth.py`**:
   ```python
   from fastapi import Depends
   from auth import get_current_user

   @router.post("/logout")
   async def logout(user_id: str = Depends(get_current_user)):
       # Stateless: just return success (client clears token)
       return {"status": "logged_out", "message": "Token cleared on client"}
   ```

2. **Test**
   ```bash
   # Get token from signin
   TOKEN=$(curl -X POST http://localhost:8000/api/auth/signin ... | jq .access_token)

   # Logout
   curl -X POST http://localhost:8000/api/auth/logout \
     -H "Authorization: Bearer $TOKEN"
   ```

**Acceptance Criteria**:
- [ ] Logout endpoint returns success
- [ ] Client removes token from storage
- [ ] Subsequent requests without token get 401
- [ ] Token expires after 30 days

**Estimated Time**: 30 minutes

---

## FINAL VERIFICATION (Day 3)

### Integration Test
```bash
# 1. Start FastAPI server
cd backend/fastapi-app
uvicorn main:app --reload

# 2. In another terminal, run tests
python -c "
import requests

# Health check
resp = requests.get('http://localhost:8000/health')
assert resp.status_code == 200
print('✓ Health check passed')

# API health (databases)
resp = requests.get('http://localhost:8000/api/health')
assert resp.status_code == 200
print('✓ API health passed')

# Signup
resp = requests.post('http://localhost:8000/api/auth/signup',
  json={'email': 'test@example.com', 'password': 'test123'})
assert resp.status_code == 200
token = resp.json()['access_token']
print('✓ Signup passed')

# Signin
resp = requests.post('http://localhost:8000/api/auth/signin',
  json={'email': 'test@example.com', 'password': 'test123'})
assert resp.status_code == 200
print('✓ Signin passed')

# Protected route
resp = requests.get('http://localhost:8000/api/user/profile',
  headers={'Authorization': f'Bearer {token}'})
assert resp.status_code == 200
print('✓ Protected route passed')

print('\n✓✓✓ ALL PHASE 0 BACKEND TESTS PASSED ✓✓✓')
"
```

---

## DELIVERABLES CHECKLIST

By end of Phase 0, you should have:

- [ ] Neon Postgres database created
  - [ ] 6 tables created (users, preferences, chat_sessions, chat_messages, chapters, user_progress)
  - [ ] Foreign keys and indexes in place
  - [ ] `.env.local` with `DATABASE_URL`

- [ ] Qdrant vector database initialized
  - [ ] Collection "chapters" created
  - [ ] Vector size 1536, distance Cosine
  - [ ] `.env.local` with `QDRANT_URL`, `QDRANT_API_KEY`

- [ ] FastAPI backend running
  - [ ] `main.py` with health endpoints
  - [ ] CORS configured for localhost:3000 + GitHub Pages
  - [ ] JSON logging working
  - [ ] `uvicorn main:app --reload` starts successfully

- [ ] SQLAlchemy ORM
  - [ ] `models.py` with all 6 models
  - [ ] Relationships configured
  - [ ] `database.py` with engine and session factory
  - [ ] `qdrant_client.py` with client

- [ ] Better-Auth
  - [ ] Installed and configured
  - [ ] Email provider set up (SendGrid or SMTP)
  - [ ] `/api/auth/signup` working
  - [ ] `/api/auth/signin` working
  - [ ] `/api/auth/logout` working

- [ ] Testing
  - [ ] All endpoints tested via curl/Python requests
  - [ ] Database connections verified
  - [ ] No critical errors

---

## REPORT BACK

When complete, provide:

1. **Status**: "Phase 0 Backend COMPLETE ✓"
2. **Databases**:
   - Neon connection string (without password)
   - Qdrant URL (without key)
   - Both tested and working
3. **Server**: FastAPI running on http://localhost:8000
4. **Endpoints**:
   - GET /health ✓
   - GET /api/health ✓
   - POST /api/auth/signup ✓
   - POST /api/auth/signin ✓
   - POST /api/auth/logout ✓
5. **Any blockers**: List any issues encountered

---

**Start Now!** You're unblocking everything else.

