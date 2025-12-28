# Quick Start Guide: RAG Chat Widget

Get the chat widget running locally in 5 minutes.

---

## Prerequisites

- **Node.js** 18+ (download from https://nodejs.org)
- **Python** 3.9+ (download from https://python.org)
- **Git**

Verify installation:
```bash
node --version  # Should be v18+
npm --version   # Should be 9+
python --version  # Should be 3.9+
```

---

## Part 1: Backend Setup (5 minutes)

### Step 1: Setup Python Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
# You need:
# - QDRANT_URL (Qdrant vector database)
# - QDRANT_API_KEY
# - OPENAI_API_KEY or OPENROUTER_API_KEY
```

### Step 4: Run Backend Server

```bash
python -m uvicorn app:app --reload --port 8000
```

**Expected output:**
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Backend is ready at: **http://localhost:8000**

Check health: `curl http://localhost:8000/health`

---

## Part 2: Frontend Setup (5 minutes)

### Step 1: Install Dependencies

```bash
cd front-end
npm install
```

This installs Docosaurus, React, TypeScript, and all dependencies.

### Step 2: Start Development Server

```bash
npm start
```

**Expected output:**
```
[INFO] Docosaurus server started on http://localhost:3000
```

Frontend is ready at: **http://localhost:3000**

---

## Part 3: Test the Chat Widget

### In Browser

1. Open http://localhost:3000
2. Look for the chat widget on the page
3. Type a question: "What is humanoid robotics?"
4. Click Send or press Ctrl+Enter

**Expected:**
- Loading state appears
- Response appears in 1-5 seconds
- Sources are listed with links
- Confidence score displayed

### Test Selected-Text Feature

1. Highlight any text in the textbook
2. Chat widget should show blue banner: "Selected: ..."
3. Click "Ask about this"
4. Query pre-fills with selected text
5. Submit and get context-aware response

### Check DevTools (F12)

**Network tab:**
- POST request to `http://localhost:8000/chat`
- Response status should be 200
- Response contains: `query`, `response`, `sources`, `confidence`

**Console:**
- No JavaScript errors
- Debug logs show (if REACT_APP_DEBUG=true)

---

## Architecture

```
Frontend (Port 3000)              Backend (Port 8000)
   React/TypeScript                  FastAPI/Python
   Docosaurus                        Qdrant + LLM
         ↓                                ↓
    localhost:3000  ←HTTP/CORS→  localhost:8000
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| **"Failed to fetch" error** | Backend not running. Check uvicorn terminal |
| **CORS error in console** | Backend port is wrong in `.env.local` |
| **Chat widget not visible** | Check browser console for JS errors (F12) |
| **Timeout waiting for response** | Backend is slow. Check `/health` endpoint |
| **Module not found error** | Run `npm install` in front-end directory |

---

## Environment Variables

### Frontend (.env.local)

```bash
REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_API_TIMEOUT=15000
REACT_APP_DEBUG=true
REACT_APP_ENABLE_SELECTED_TEXT=true
REACT_APP_ENABLE_SYNTHESIS=true
```

### Backend (.env)

```bash
QDRANT_URL=your-qdrant-url
QDRANT_API_KEY=your-key
OPENAI_API_KEY=your-key
OPENROUTER_API_KEY=your-key
LOG_LEVEL=INFO
```

---

## Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend | 8000 | http://localhost:8000 |
| Health Check | 8000 | http://localhost:8000/health |

---

## Next Steps

- For deployment: see [DEPLOYMENT_GUIDE.md](../../DEPLOYMENT_GUIDE.md)
- For demo script: see [DEMO_SCRIPT.md](./DEMO_SCRIPT.md)
- For architecture: see [README.md](./README.md)

**Status**: Ready to develop! 🚀
