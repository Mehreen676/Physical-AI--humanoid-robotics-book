# Phase 0 Complete Setup Guide

**Status**: ✅ Code complete | ⏳ Databases pending configuration

This guide walks you through completing Phase 0 by setting up databases and environment variables.

---

## Step 1: Set Up Neon Postgres Database

### Create Neon Account & Database

1. **Go to**: https://neon.tech
2. **Sign up** (GitHub or email)
3. **Create project**:
   - Project name: `physical-ai-textbook`
   - Region: Choose closest to you
4. **Copy connection string**:
   - Navigate to "Connection strings"
   - Copy **Pooled connection string** (appears as `postgresql://...`)

### Example Connection String
```
postgresql://neon_user:password123@ep-example-region.neon.tech/dbname?sslmode=require
```

**Connection Details You'll See**:
```
Host: ep-example-region.neon.tech
Database: neon_dbname
User: neon_user
Password: [random password]
Port: 5432
```

---

## Step 2: Set Up Qdrant Vector Database

### Option A: Qdrant Cloud (Recommended for Production)

1. **Go to**: https://cloud.qdrant.io
2. **Sign up** (free tier available)
3. **Create cluster**:
   - Name: `physical-ai-vectors`
   - Region: Choose closest to you
   - Size: Free tier or small cluster
4. **Copy API details**:
   - Cluster URL: `https://[cluster-id].eu-west-1-0.aws.qdrant.io`
   - API Key: [auto-generated]

### Option B: Local Qdrant (For Development)

```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant:latest

# Or download from: https://qdrant.tech/documentation/quick-start/
```

**Local connection**:
```
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Leave empty for local
```

---

## Step 3: Get OpenAI API Key

1. **Go to**: https://platform.openai.com/api-keys
2. **Create new secret key**:
   - Click "Create new secret key"
   - Copy immediately (won't show again)
3. **Ensure you have**:
   - ✅ GPT-4 access
   - ✅ Embeddings API access

**Test your key**:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Step 4: Set Up SendGrid Email Service

1. **Go to**: https://sendgrid.com
2. **Sign up** (free tier: 100 emails/day)
3. **Create API key**:
   - Settings → API Keys → Create API Key
   - Name: `physical-ai-textbook`
   - Copy the key
4. **Verify sender email**:
   - Settings → Sender Authentication
   - Add and verify `no-reply@yourdomain.com` (or use SendGrid's default)

**Test SendGrid**:
```bash
curl --request POST \
  --url https://api.sendgrid.com/v3/mail/send \
  --header "Authorization: Bearer $SENDGRID_API_KEY" \
  --header "Content-Type: application/json"
```

---

## Step 5: Configure Environment Variables

### Copy Template
```bash
cd physical-ai-humanoid-robotics-book
cp .env.example .env.local
```

### Edit `.env.local`

Open `.env.local` in your editor and fill in:

```bash
# ===== DATABASE =====
DATABASE_URL=postgresql://[user]:[password]@[host]:5432/[dbname]?sslmode=require

# Example from Neon:
# DATABASE_URL=postgresql://neon_user:password123@ep-example-region.neon.tech/dbname?sslmode=require

# ===== QDRANT VECTOR DATABASE =====
QDRANT_URL=https://[cluster-id].eu-west-1-0.aws.qdrant.io
# OR for local:
# QDRANT_URL=http://localhost:6333

QDRANT_API_KEY=your-qdrant-api-key-here
# Leave blank if using local Qdrant

# ===== OPENAI API =====
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# ===== SENDGRID EMAIL =====
SENDGRID_API_KEY=SG.your-key-here
SENDGRID_FROM_EMAIL=no-reply@textbook.example.com

# ===== AUTHENTICATION =====
JWT_SECRET=your-random-secret-key-min-32-chars-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=30

BETTER_AUTH_SECRET=your-better-auth-secret-change-in-production

# ===== SERVER =====
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# ===== FRONTEND =====
FRONTEND_URL=http://localhost:3000

# ===== OPTIONAL =====
# SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

### Generate Secure Secrets

```bash
# Generate JWT_SECRET (32+ chars)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate BETTER_AUTH_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Step 6: Verify All Connections

### Test Database

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Test connection
python -c "
from app.core.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('✓ Postgres connection successful')
except Exception as e:
    print(f'✗ Postgres connection failed: {e}')
"
```

### Test Qdrant

```bash
# Test connection
python -c "
from qdrant_client import QdrantClient
from app.core.config import settings

try:
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
    )
    collections = client.get_collections()
    print('✓ Qdrant connection successful')
    print(f'  Collections: {len(collections.collections)}')
except Exception as e:
    print(f'✗ Qdrant connection failed: {e}')
"
```

### Test OpenAI

```bash
# Test API key
python -c "
from openai import OpenAI
from app.core.config import settings

try:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    models = client.models.list()
    print('✓ OpenAI API connection successful')
    print(f'  Available models: {len(models.data)}')
except Exception as e:
    print(f'✗ OpenAI API connection failed: {e}')
"
```

---

## Step 7: Initialize Database Tables

```bash
cd backend

# Activate venv
source venv/bin/activate

# Run Python
python -c "
from app.core.database import init_db
try:
    init_db()
    print('✓ Database tables created successfully')
except Exception as e:
    print(f'✗ Failed to create tables: {e}')
"
```

**Or in Python shell**:
```bash
python

>>> from app.core.database import init_db
>>> init_db()
✓ Database tables initialized
```

---

## Step 8: Create Qdrant Collection

```bash
python -c "
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from app.core.config import settings

try:
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
    )

    # Create collection for chapter embeddings
    client.create_collection(
        collection_name='chapters',
        vectors_config=VectorParams(
            size=1536,  # OpenAI text-embedding-3-small
            distance=Distance.COSINE
        )
    )
    print('✓ Qdrant collection created: chapters')
except Exception as e:
    if 'already exists' in str(e):
        print('✓ Qdrant collection already exists: chapters')
    else:
        print(f'✗ Failed to create collection: {e}')
"
```

---

## Step 9: Start Backend Server

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate

# Run development server
uvicorn app.main:app --reload --port 8000
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Test endpoints**:
```bash
# Health check
curl http://localhost:8000/health
# Response: {"status": "ok", "service": "...", "version": "0.1.0"}

# Detailed health
curl http://localhost:8000/api/health
# Response: {"status": "healthy", "postgres": "ok", "qdrant": "ok", ...}
```

**View API docs**:
- Open: http://localhost:8000/api/docs
- Swagger UI with interactive testing

---

## Step 10: Test Authentication Endpoints

### Signup

```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "background_software": "Intermediate",
    "learning_goal": "Career"
  }'
```

**Expected response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 2592000
}
```

### Signin

```bash
curl -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

### Get Profile

```bash
# Replace TOKEN with the access_token from signup/signin
TOKEN="eyJhbGciOiJIUzI1NiIs..."

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/auth/me
```

**Expected response**:
```json
{
  "id": "uuid-here",
  "email": "test@example.com",
  "background_software": "Intermediate",
  "learning_goal": "Career",
  "preferred_language": "en",
  "difficulty_level": "Intermediate",
  "email_verified": false,
  "created_at": "2025-12-24T10:30:00Z"
}
```

---

## Step 11: Start Frontend Development Server

```bash
cd docusaurus-site

# Install dependencies
npm install

# Start dev server
npm run start
```

**Expected output**:
```
[INFO] Docusaurus 3.x server running at http://localhost:3000
```

**Verify**:
- Open: http://localhost:3000
- Should see Docusaurus default homepage
- Navbar, sidebar, footer visible

---

## Phase 0 Completion Checklist

### ✅ Code Setup
- [x] Git repository on main branch
- [x] Docusaurus initialized
- [x] FastAPI backend skeleton
- [x] Database models defined
- [x] Authentication endpoints
- [x] Health checks
- [x] GitHub Actions workflows
- [x] Environment template

### ⏳ Database Setup (Complete these now)
- [ ] Neon Postgres account created
- [ ] Database connection string in .env.local
- [ ] Postgres tables initialized (`init_db()`)
- [ ] Database connectivity verified

### ⏳ Vector Database Setup
- [ ] Qdrant account/instance created
- [ ] API key/URL in .env.local
- [ ] Qdrant collection created (`chapters`)
- [ ] Qdrant connectivity verified

### ⏳ API Keys & Services
- [ ] OpenAI API key in .env.local
- [ ] SendGrid API key in .env.local
- [ ] JWT secrets generated and set
- [ ] All keys tested

### ⏳ Local Testing
- [ ] Backend server runs (`uvicorn app.main:app`)
- [ ] Health endpoints respond
- [ ] Signup endpoint works
- [ ] Signin endpoint works
- [ ] Get profile endpoint works
- [ ] API docs load at /api/docs

### ⏳ Frontend Testing
- [ ] `npm install` completes
- [ ] `npm run start` runs
- [ ] Frontend accessible at localhost:3000
- [ ] Navbar, sidebar, footer render

### ✅ Git/GitHub
- [ ] Code committed to main branch
- [ ] GitHub Actions configured
- [ ] Secrets configured in GitHub (for deployment)

---

## Troubleshooting

### Postgres Connection Error
```
Error: could not connect to server
```
**Solutions**:
1. Verify `DATABASE_URL` format in `.env.local`
2. Check Neon credentials are correct
3. Whitelist your IP in Neon dashboard
4. Test: `psql $DATABASE_URL`

### Qdrant Connection Error
```
Error: Failed to connect to Qdrant
```
**Solutions**:
1. Verify `QDRANT_URL` is correct
2. Check `QDRANT_API_KEY` (if cloud)
3. If local: ensure Docker container running
4. Test: `curl $QDRANT_URL/health`

### OpenAI API Error
```
Error: Invalid API key
```
**Solutions**:
1. Verify key format: `sk-proj-...`
2. Check key is active in OpenAI dashboard
3. Ensure GPT-4 access enabled
4. Verify key not expired

### Auth Token Error
```
Error: Invalid authentication credentials
```
**Solutions**:
1. Verify token not expired (30 days)
2. Check `JWT_SECRET` matches
3. Try signing in again
4. Check token format: `Bearer <token>`

### Database Initialization Error
```
Error: Failed to initialize database
```
**Solutions**:
1. Verify Postgres is accessible
2. Check database user has CREATE TABLE permission
3. Drop existing tables if corrupted: `DROP TABLE users CASCADE;`
4. Run `init_db()` again

---

## Next Steps After Phase 0

### Phase 1: MVP Development (Weeks 2-5)

1. **Write 12 Chapters** (@Educator + @RoboticsExpert)
   - Module 1: ROS 2 (3 chapters)
   - Module 2: Gazebo/Unity (3 chapters)
   - Module 3: NVIDIA Isaac (3 chapters)
   - Module 4: VLA (3 chapters)

2. **Build Custom Docusaurus Theme** (@FrontendEngineer)
   - Disable defaults
   - Implement Navbar, Sidebar, Footer
   - Set up Tailwind CSS
   - 20+ reusable components

3. **Implement RAG Chatbot** (@BackendEngineer)
   - Embedding service (OpenAI)
   - Qdrant retrieval
   - Ranking & filtering
   - GPT-4 generation

4. **Integrate Authentication** (@AuthPersonalizer)
   - Email verification (SendGrid)
   - User profiling
   - Session management

---

## Quick Reference Commands

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend setup
cd docusaurus-site
npm install
npm run start

# Database operations
python -c "from app.core.database import init_db; init_db()"

# Create Qdrant collection
python scripts/setup_qdrant.py

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/docs

# Push to GitHub
git push origin main
```

---

## Resources

- **Neon Postgres**: https://neon.tech/docs
- **Qdrant**: https://qdrant.tech/documentation/
- **FastAPI**: https://fastapi.tiangolo.com/
- **OpenAI API**: https://platform.openai.com/docs/guides
- **SendGrid**: https://docs.sendgrid.com/
- **Docusaurus**: https://docusaurus.io/docs

---

**Status**: Phase 0 code ready | Awaiting database configuration

**Estimated Time**: 30 minutes to complete all setup steps

**Next Check**: Once all steps complete, Phase 1 begins!
