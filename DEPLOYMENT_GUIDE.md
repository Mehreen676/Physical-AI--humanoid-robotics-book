# Deployment Guide: RAG Chat Widget

This guide covers deploying the RAG Chat Widget to GitHub Pages with a backend FastAPI service.

## Architecture Overview

```
GitHub Pages (Frontend)
├── Docusaurus site + React components
├── ChatWidget component
├── Chat services & hooks
└── TypeScript configuration

     ↓ HTTP requests (CORS enabled)

Backend Service (FastAPI)
├── Chat router (/chat endpoint)
├── RAG agent integration
├── Qdrant vector store
├── LLM provider (OpenAI/OpenRouter)
└── Health checks
```

## Prerequisites

- Node.js 18+ (for frontend)
- Python 3.9+ (for backend)
- Git and GitHub account
- GitHub Pages enabled on repository
- CORS-enabled backend deployment

## Part 1: Frontend Deployment (GitHub Pages)

### Step 1: Update Production Backend URL

The ChatWidget needs to know where your backend service is deployed. Environment variables are baked into the build at compile time.

**Edit `front-end/.env.production`:**
```bash
# Replace this with your actual backend URL
REACT_APP_BACKEND_URL=https://your-deployed-backend-url.com
```

### Examples of backend deployment options:

1. **Railway** (recommended for simplicity)
   - Deploy FastAPI service to Railway
   - Get service URL: `https://your-app-name.up.railway.app`

2. **Heroku**
   - Deploy FastAPI service to Heroku
   - Get service URL: `https://your-app.herokuapp.com`

3. **Self-hosted (VPS/Server)**
   - Deploy to your own server/VM
   - Configure DNS and get URL: `https://your-domain.com`

4. **Local testing** (during development)
   - Backend on localhost: `http://your-machine-ip:8000`
   - Only works if both frontend and backend are on same network

### Step 2: Build for Production

```bash
cd front-end

# Install dependencies (if not already done)
npm install

# Build production bundle with .env.production variables
npm run build
```

This creates an optimized build in `front-end/build/` with environment variables baked in.

### Step 3: Deploy to GitHub Pages

```bash
# From front-end directory
npm run deploy
```

This uses `gh-pages` to:
1. Push the build directory to `gh-pages` branch
2. GitHub automatically serves it at your GitHub Pages URL
3. Site is live at: `https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/`

### Step 4: Verify Deployment

1. Visit your GitHub Pages URL
2. Open browser DevTools (F12)
3. Check Network tab for `/chat` requests
4. Verify requests go to the correct backend URL from `.env.production`

**Common issues:**
- "Failed to fetch" = Backend URL wrong or backend is down
- "CORS error" = Backend CORS not configured for GitHub Pages origin
- 404 errors = Backend endpoint not implemented

---

## Part 2: Backend Deployment

### Option A: Deploy to Railway (Recommended)

**Why Railway?**
- Easy integration with GitHub
- One-click deployment
- Free tier available
- Simple environment variable management

**Steps:**

1. **Create Railway account**: https://railway.app

2. **Connect GitHub repository**
   - Railway Dashboard → New Project → Deploy from GitHub repo

3. **Configure environment variables** in Railway dashboard:
   - Copy all variables from `backend/.env`:
     - `QDRANT_URL`
     - `QDRANT_API_KEY`
     - `COHERE_API_KEY`
     - `OPENAI_API_KEY`
     - `OPENROUTER_API_KEY`
     - `LOG_LEVEL=INFO`
     - `BATCH_SIZE=50`
     - `CHUNK_SIZE=1000`
     - `CHUNK_OVERLAP=100`
     - `COLLECTION_NAME=rag_embedding`
     - `OPENROUTER_URL=https://openrouter.ai/api/v1/chat/completions`
     - `MODEL_NAME=mistralai/devstral-2512:free`

4. **Set Python version** (if prompted)
   - Select Python 3.11+

5. **Configure startup command**
   ```bash
   python -m uvicorn app:app --host 0.0.0.0 --port $PORT
   ```

6. **Get service URL**
   - Copy the generated URL (e.g., `https://your-app-name.up.railway.app`)

7. **Update frontend .env.production**
   - Set `REACT_APP_BACKEND_URL=https://your-app-name.up.railway.app`
   - Rebuild and redeploy frontend

### Option B: Deploy to Heroku

**Steps:**

1. **Create Heroku account**: https://heroku.com

2. **Install Heroku CLI**:
   ```bash
   npm install -g heroku
   ```

3. **Login and create app**:
   ```bash
   heroku login
   heroku create your-app-name
   ```

4. **Configure environment variables**:
   ```bash
   heroku config:set QDRANT_URL=your-qdrant-url
   heroku config:set QDRANT_API_KEY=your-key
   heroku config:set OPENAI_API_KEY=your-key
   # ... add all other variables
   ```

5. **Deploy**:
   ```bash
   git push heroku main
   ```

6. **Get service URL**:
   ```bash
   heroku apps:info your-app-name
   ```

### Option C: Self-hosted

1. **Choose hosting** (VPS, dedicated server, etc.)
   - DigitalOcean, AWS, Google Cloud, Azure, etc.

2. **Setup Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   # Create backend/.env with all required variables
   export QDRANT_URL=...
   export QDRANT_API_KEY=...
   # ... etc
   ```

4. **Run application**:
   ```bash
   python -m uvicorn app:app --host 0.0.0.0 --port 8000
   ```

5. **Setup reverse proxy** (nginx/Apache)
   - Configure SSL/TLS certificate
   - Point domain to your server

6. **Configure systemd service** (for auto-restart):
   ```ini
   [Unit]
   Description=RAG Chat Service
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/backend
   Environment="PATH=/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

---

## Part 3: Backend CORS Configuration

### Current CORS Setup

The backend (`backend/app.py`) is configured to accept requests from:

```python
cors_origins = [
    "http://localhost:3000",           # Local dev
    "http://localhost:8000",           # Alt local dev
    "http://127.0.0.1:3000",           # Localhost IP
    "https://mehreen676.github.io",    # GitHub Pages
]
```

### For your own GitHub Pages deployment

**Update `backend/app.py` CORS configuration:**

```python
# Add your GitHub Pages URL to cors_origins
cors_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "https://YOUR-USERNAME.github.io",  # Your GitHub Pages URL
]
```

**Or use environment variable** (recommended for multiple deployments):

```python
import os

cors_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    os.getenv("ALLOWED_ORIGIN", "https://mehreen676.github.io"),
]
```

Then set in backend environment:
```bash
ALLOWED_ORIGIN=https://YOUR-USERNAME.github.io
```

---

## Part 4: Testing Deployment

### Health Check

Test that backend is running:

```bash
curl https://your-backend-url.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "RAG Chat Service is running"
}
```

### Full Chat Query Test

```bash
curl -X POST https://your-backend-url.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is humanoid robotics?",
    "k": 5
  }'
```

### Browser Testing

1. Visit: `https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/`
2. Open DevTools → Network tab
3. Type a question in the chat widget
4. Watch for successful `/chat` request
5. Response should appear in chat

**Debug CORS errors:**
- Check backend CORS origins include your GitHub Pages URL
- Verify backend is actually running and accessible
- Check browser console for detailed error messages

---

## Part 5: Deployment Checklist

### Pre-deployment

- [ ] Backend service deployed and running
- [ ] Backend `/health` endpoint responds with 200
- [ ] Backend CORS configured for GitHub Pages origin
- [ ] All backend environment variables set (API keys, Qdrant, etc.)
- [ ] Frontend `.env.production` has correct backend URL

### Deployment

- [ ] Run `npm run build` in front-end directory
- [ ] Verify build completes without errors
- [ ] Run `npm run deploy` to push to GitHub Pages
- [ ] Monitor deployment (check Actions tab in GitHub)

### Post-deployment

- [ ] GitHub Pages site loads without 404 errors
- [ ] Chat widget is visible and interactive
- [ ] Sending a query works (watch Network tab)
- [ ] Response displays correctly with sources
- [ ] Selected text feature works (if enabled)
- [ ] No console errors (F12 → Console tab)

### Production Monitoring

- [ ] Monitor backend logs for errors
- [ ] Check backend resource usage (CPU, memory)
- [ ] Monitor response times (target: < 5 seconds)
- [ ] Track API errors and failures
- [ ] Set up alerts for backend downtime

---

## Troubleshooting

### "Failed to fetch" error

**Possible causes:**
1. Backend URL wrong in `.env.production`
2. Backend is not running
3. Backend URL is unreachable

**Fix:**
```bash
# Verify backend is running
curl https://your-backend-url.com/health

# Check .env.production has correct URL
cat front-end/.env.production

# Rebuild and redeploy
cd front-end
npm run build
npm run deploy
```

### CORS errors in console

**Error:** `Access to XMLHttpRequest blocked by CORS policy`

**Cause:** Backend CORS doesn't include GitHub Pages origin

**Fix in `backend/app.py`:**
```python
cors_origins = [
    # ... existing origins ...
    "https://YOUR-USERNAME.github.io",  # Add this line
]
```

Then redeploy backend.

### Chat widget doesn't appear

**Possible causes:**
1. JavaScript error (check console)
2. Component not imported in Docusaurus pages
3. TypeScript compilation error

**Fix:**
- Check browser console for JavaScript errors
- Ensure ChatWidget is imported in page where it's used
- Verify TypeScript builds: `npm run build` should have no errors

### Slow responses (> 10 seconds)

**Possible causes:**
1. Backend is overloaded
2. Qdrant vector store is slow
3. LLM API is slow
4. Network latency

**Actions:**
- Check backend logs for errors
- Monitor Qdrant performance
- Check LLM API status
- Increase API timeout in `.env.production`: `REACT_APP_API_TIMEOUT=30000`

---

## Production Best Practices

1. **Use environment variables** for all secrets
   - Never commit API keys to git
   - Use `.env` and `.gitignore`

2. **Monitor backend health**
   - Check logs regularly
   - Set up alerts for errors
   - Monitor API rate limits

3. **Cache where possible**
   - Use CDN for static assets (GitHub Pages does this)
   - Cache LLM responses if possible

4. **Update dependencies**
   - Keep Node packages updated: `npm audit fix`
   - Keep Python packages updated: `pip list --outdated`

5. **Use HTTPS everywhere**
   - All connections should be secure
   - GitHub Pages auto-provides HTTPS
   - Backend should use HTTPS (not HTTP)

6. **Test regularly**
   - Test deployment changes in staging first
   - Keep integration tests running
   - Monitor real user queries for quality

---

## Support & Issues

- **Frontend issues**: Check Docusaurus docs
- **Backend issues**: Check FastAPI docs
- **Deployment issues**: Check platform-specific guides
- **CORS issues**: Use browser DevTools Network tab to debug

---

**Status**: Production ready
**Last updated**: 2025-12-28
