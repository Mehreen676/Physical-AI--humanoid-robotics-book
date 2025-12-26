# Next Steps - Phase 0 Completion

**Status**: Code ✅ Ready | Databases ⏳ Pending Configuration

---

## 🎯 Your Immediate Task List

### Step 1: Get 4 Credentials (20 minutes)

**Credential #1: Neon Postgres**
```
👉 Go to: https://console.neon.tech
1. Sign in
2. Click your project → Connection strings
3. Copy "Pooled connection string"
4. Paste into ENV-SETUP-QUICK-REFERENCE.md to remember format
```

**Credential #2: Qdrant**
```
👉 Go to: https://cloud.qdrant.io
1. Sign in
2. Click your cluster
3. Copy "API Key" and "URL"
4. Paste both into ENV-SETUP-QUICK-REFERENCE.md
```

**Credential #3: OpenAI API**
```
👉 Go to: https://platform.openai.com/api-keys
1. Sign in
2. Click "Create new secret key"
3. Copy immediately (won't show again!)
4. Paste into ENV-SETUP-QUICK-REFERENCE.md
```

**Credential #4: JWT Secrets**
```
👉 Open terminal and run:
python -c "import secrets; print(secrets.token_urlsafe(32))"
1. Copy output → this is JWT_SECRET
2. Run again → this is BETTER_AUTH_SECRET
3. Paste both into ENV-SETUP-QUICK-REFERENCE.md
```

---

### Step 2: Fill .env.local (5 minutes)

```bash
# In your IDE, open: .env.local

# Copy this entire block below and paste:
```

```bash
# ===== DATABASE (from Credential #1) =====
DATABASE_URL=postgresql://neon_user:abc123@ep-example.neon.tech/dbname?sslmode=require

# ===== QDRANT (from Credential #2) =====
QDRANT_URL=https://12345678-abcd.eu-west-1-0.aws.qdrant.io
QDRANT_API_KEY=aBcDeFgHiJkLmNoPqRsTuVwXyZ

# ===== OPENAI (from Credential #3) =====
OPENAI_API_KEY=sk-proj-abc123def456
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# ===== SENDGRID (Optional, can do later) =====
SENDGRID_API_KEY=SG.your-key
SENDGRID_FROM_EMAIL=no-reply@example.com

# ===== AUTHENTICATION (from Credential #4) =====
JWT_SECRET=your-random-secret-from-python
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=30

BETTER_AUTH_SECRET=another-random-secret-from-python

# ===== SERVER =====
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# ===== FRONTEND =====
FRONTEND_URL=http://localhost:3000
```

---

### Step 3: Start Backend (2 minutes)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate    # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database tables
python -c "from app.core.database import init_db; init_db()"

# Start server
uvicorn app.main:app --reload
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

### Step 4: Test Backend (2 minutes)

**In a new terminal** (keep backend running):

```bash
# Test health check
curl http://localhost:8000/health

# Response should be:
# {"status": "ok", "service": "Physical AI Textbook Backend", "version": "0.1.0"}
```

**Or open in browser**:
```
http://localhost:8000/api/docs
```
You should see Swagger UI with all endpoints!

---

### Step 5: Start Frontend (2 minutes)

**In a new terminal** (keep backend running):

```bash
cd docusaurus-site

# Install dependencies
npm install

# Start dev server
npm run start
```

**Expected output**:
```
✔ Compiled client successfully
✔ Docusaurus server running at http://localhost:3000
```

**Or open in browser**:
```
http://localhost:3000
```

---

### Step 6: Test Everything Works (3 minutes)

**Test 1: Health Check API**
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok", ...}
```

**Test 2: API Documentation**
```
Open: http://localhost:8000/api/docs
Click "Try it out" on any endpoint
```

**Test 3: Frontend Load**
```
Open: http://localhost:3000
Should see Docusaurus site with navbar, sidebar, footer
```

**Test 4: User Signup**
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "background_software": "Intermediate"
  }'

# Should return:
# {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 2592000}
```

---

## ✅ Phase 0 Completion Checklist

Print this and check off as you go:

```
CREDENTIALS (Step 1)
- [ ] Neon Postgres connection string
- [ ] Qdrant URL
- [ ] Qdrant API Key
- [ ] OpenAI API key
- [ ] JWT_SECRET (python generated)
- [ ] BETTER_AUTH_SECRET (python generated)

CONFIGURATION (Step 2)
- [ ] .env.local file created
- [ ] All credentials filled in
- [ ] File saved

BACKEND SETUP (Step 3)
- [ ] venv created
- [ ] pip install completed
- [ ] Database tables initialized
- [ ] Server running (uvicorn)

BACKEND TESTING (Step 4)
- [ ] /health endpoint responds
- [ ] /api/health endpoint responds
- [ ] API docs load at /api/docs
- [ ] Signup endpoint works

FRONTEND SETUP (Step 5)
- [ ] npm install completed
- [ ] Server running (npm start)
- [ ] Frontend loads at localhost:3000

FINAL VERIFICATION (Step 6)
- [ ] Health checks passing
- [ ] API docs accessible
- [ ] Frontend renders correctly
- [ ] Signup works end-to-end
```

---

## 🚨 If Something Goes Wrong

### Backend won't start
```
Error: ModuleNotFoundError: No module named 'app'

Solution:
1. Make sure you're in 'backend' directory
2. Check venv is activated
3. Run: pip install -r requirements.txt
```

### Database connection error
```
Error: could not connect to server

Solutions:
1. Check DATABASE_URL in .env.local
2. Verify Neon credentials are correct
3. Check your IP is whitelisted in Neon dashboard
4. Test: psql $DATABASE_URL
```

### API key errors
```
Error: Invalid API key provided

Solutions:
1. Re-copy the key (don't edit it)
2. Check for extra spaces before/after
3. Verify key is active in provider dashboard
4. Re-generate key if needed
```

### Frontend won't load
```
Error: npm: command not found

Solutions:
1. Install Node.js from nodejs.org
2. Check: node --version
3. Check: npm --version
```

---

## 📞 Quick Support

| Issue | Fix |
|-------|-----|
| Port 8000 already in use | Change SERVER_PORT in .env.local |
| Port 3000 already in use | Run: `npm run start -- --port 3001` |
| Database locked | Stop all backend instances |
| CORS error | Check FRONTEND_URL in .env.local |
| Token invalid | Re-signin to get new token |

---

## 🎉 Success Indicators

✅ When everything is working:

1. Backend server running
   ```
   Uvicorn running on http://0.0.0.0:8000
   Application startup complete
   ```

2. Frontend server running
   ```
   Docusaurus server running at http://localhost:3000
   ```

3. Health checks passing
   ```bash
   curl http://localhost:8000/api/health
   # {"status": "healthy", "postgres": "ok", "qdrant": "ok", ...}
   ```

4. API docs accessible
   ```
   http://localhost:8000/api/docs (Swagger UI)
   ```

5. Signup works
   ```bash
   curl -X POST http://localhost:8000/api/auth/signup ...
   # Returns JWT token
   ```

---

## ⏱️ Timeline

| Task | Duration | Status |
|------|----------|--------|
| Get 4 credentials | 20 min | 👈 **YOU ARE HERE** |
| Fill .env.local | 5 min | ⏳ Next |
| Setup backend | 5 min | ⏳ Next |
| Test backend | 3 min | ⏳ Next |
| Setup frontend | 5 min | ⏳ Next |
| Final verification | 5 min | ⏳ Next |
| **TOTAL** | **~45 min** | ⏳ |

---

## 🚀 After Phase 0 Complete

Once all tests pass:

1. **Phase 1 begins** (Weeks 2-5)
   - Write 12 chapters
   - Build custom Docusaurus theme
   - Implement RAG chatbot

2. **Live deployment**
   - Frontend auto-deploys to GitHub Pages
   - Backend can deploy to Railway/Vercel

3. **Invite collaborators**
   - @FrontendEngineer for UI work
   - @BackendEngineer for chatbot
   - @Educator for chapter writing

---

## 📚 Reference Documents

- **ENV-SETUP-QUICK-REFERENCE.md** - Credential details
- **PHASE-0-SETUP-GUIDE.md** - Detailed step-by-step
- **ARCHITECTURE.md** - System design
- **backend/README.md** - Backend documentation
- **PLAN.md** - Overall implementation plan

---

## 💬 Current Status

```
┌─────────────────────────────────────┐
│ PHASE 0 CODE: ✅ COMPLETE           │
│ PHASE 0 SETUP: ⏳ IN PROGRESS       │
│                                     │
│ You are at Step 1 of 6              │
│ Time remaining: ~40 minutes         │
└─────────────────────────────────────┘
```

---

## ✨ Final Note

**You're almost there!**

The hard part (architecture, code, planning) is done. Now it's just configuration—copy/paste credentials and run commands.

Once Phase 0 is complete, you'll have:
- ✅ Live frontend (GitHub Pages)
- ✅ Running backend API
- ✅ Working authentication
- ✅ Production-ready foundation
- ✅ Ready for Phase 1

**Start with Step 1 above. You've got this!** 🚀

---

**Next document to read**: ENV-SETUP-QUICK-REFERENCE.md (for detailed credential info)

**Questions?** Check PHASE-0-SETUP-GUIDE.md for detailed explanations
