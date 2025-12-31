# Deployment Guide

Complete guide for deploying BookRAGAgent to Render using Docker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Docker Testing](#local-docker-testing)
3. [Render Deployment](#render-deployment)
4. [Troubleshooting](#troubleshooting)
5. [Monitoring & Logs](#monitoring--logs)
6. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required Services

1. **Qdrant Cloud** (Vector Database)
   - Account: https://qdrant.com/
   - Create a cluster
   - Note: URL (e.g., `https://xxx.gcp.cloud.qdrant.io:6333`)
   - Generate: API Key

2. **OpenRouter** (LLM Provider)
   - Account: https://openrouter.io/
   - Generate: API Key
   - Model: `claude-3-5-sonnet` (default)

3. **Neon** (PostgreSQL Database)
   - Account: https://neon.tech/
   - Create project
   - Get: Connection string (`postgresql://...`)

4. **Render** (Hosting)
   - Account: https://render.com/
   - Connect: GitHub repository
   - Deployment target

### GitHub Repository

```bash
# Ensure these files are committed:
- Dockerfile
- .dockerignore
- render.yaml
- .env.example
- README.md
- DEPLOYMENT.md
- backend/main.py
- backend/requirements.txt
- All application code in /backend
```

**CRITICAL**: Never commit `.env` file to Git!

---

## Local Docker Testing

### Build the Image

```bash
cd /project/root

# Build with tag
docker build -t bookrag:latest .

# Build with version tag (optional)
docker build -t bookrag:v1.0 .
```

**Expected Output**:
```
...
Successfully built xxxxx
Successfully tagged bookrag:latest
```

### Verify Image

```bash
# Check image size (should be < 500MB)
docker images bookrag:latest

# Inspect layers
docker inspect bookrag:latest

# Check image details
docker image ls --no-trunc bookrag:latest
```

### Run Container Locally

```bash
# Basic run (port 10000)
docker run -p 10000:10000 bookrag:latest

# Run with environment variables
docker run -p 10000:10000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e QDRANT_URL=https://xxx.gcp.cloud.qdrant.io:6333 \
  -e QDRANT_API_KEY=your-key \
  -e OPENROUTER_API_KEY=your-key \
  bookrag:latest

# Run in background
docker run -d -p 10000:10000 \
  --name bookrag-test \
  -e DATABASE_URL=... \
  bookrag:latest

# View logs
docker logs bookrag-test
docker logs -f bookrag-test  # Follow logs
```

### Test Endpoints

```bash
# Health check
curl http://localhost:10000/

# Health endpoint
curl http://localhost:10000/health

# Create session
curl -X POST http://localhost:10000/sessions

# View detailed response
curl -s http://localhost:10000/health | python -m json.tool
```

### Cleanup

```bash
# Stop container
docker stop bookrag-test

# Remove container
docker rm bookrag-test

# Remove image
docker rmi bookrag:latest
```

---

## Render Deployment

### Step 1: Connect GitHub Repository

1. Log in to https://render.com/
2. Click **"New +"** button (top right)
3. Select **"Web Service"**
4. Connect to GitHub account (if not already connected)
5. Select repository: `text-book` (or your repo name)
6. Click **"Connect"**

### Step 2: Configure Service

Fill in the configuration form:

| Field | Value |
|-------|-------|
| Name | `bookrag-api` |
| Environment | **Docker** |
| Build Command | (leave empty - auto-detected) |
| Start Command | (leave empty - uses Dockerfile CMD) |
| Plan | **Starter** (free) or **Standard** (paid) |
| Region | **Oregon** (or nearest to your location) |

### Step 3: Configure Environment Variables

Click the **"Environment"** tab.

Add each variable (DO NOT use `.env` file):

```
DATABASE_URL=postgresql://user:password@host/dbname
QDRANT_URL=https://xxx.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
COLLECTION_NAME=book-chunks
MODEL_NAME=claude-3-5-sonnet
LOG_LEVEL=INFO
```

**⚠️ CRITICAL**:
- Set variables in Render dashboard, NOT in `.env`
- Never commit `.env` to Git
- Use "Sync" button to update from `.env` if needed (still not recommended)

### Step 4: Create Service

1. Review all settings
2. Click **"Create Web Service"**
3. Wait for build (usually 2-3 minutes)

**Build Progress**:
```
Building... [███░░░░░░] 30%
...
Successfully deployed to: https://bookrag-api.onrender.com
```

---

## Verify Deployment

### After Deployment Complete

```bash
# Test health endpoint
curl https://bookrag-api.onrender.com/health

# Check response
curl -s https://bookrag-api.onrender.com/health | python -m json.tool

# Create a session
curl -X POST https://bookrag-api.onrender.com/sessions

# List all endpoints
curl https://bookrag-api.onrender.com/openapi.json
```

### View Logs in Render Dashboard

1. Log in to Render
2. Select **"bookrag-api"** service
3. Click **"Logs"** tab
4. View real-time output

**Expected Logs**:
```
2025-12-30 18:00:00 - main - INFO - BookRAGAgent starting up...
2025-12-30 18:00:10 - storage.init_db - INFO - Database schema initialized
2025-12-30 18:00:11 - main - INFO - Session manager initialized
...
INFO:     Application startup complete.
```

---

## Troubleshooting

### Build Fails: "No such file or directory: Dockerfile"

**Cause**: Dockerfile not in repository root

**Fix**:
```bash
# Ensure Dockerfile is in project root (not in /backend)
ls -la Dockerfile

# Verify Dockerfile path in Render dashboard
# Should show: ./Dockerfile
```

### Build Fails: "ModuleNotFoundError: No module named 'backend'"

**Cause**: Python imports expect `backend` package but it's not installed

**Fix** (in Dockerfile):
```dockerfile
# Copy structure preserved
COPY backend/ .
# NOT: COPY backend/* .
```

### Container Crashes: "Application startup failed"

**Check Logs**:
```
ERROR:    [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)
```

**Cause**: Port 8000 in main.py, but Render expects 10000

**Fix** (in main.py):
```python
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=10000  # Use 10000 for Render
    )
```

### Health Check Fails

**Symptom**: Service shows as "crashed" in Render

**Check**:
```bash
# Manually test health endpoint
curl https://your-service.onrender.com/health

# If 500 error, check logs for startup errors
# If timeout, service may not be running
```

**Common Causes**:
- Database connection fails
- Missing environment variables
- Port binding issue

### Database Connection Error

**Error**: `could not translate host name "host" to address`

**Fix**:
- Verify `DATABASE_URL` is correct
- Check Neon dashboard for connection string
- Ensure IP whitelist allows Render servers

**Test Connection**:
```bash
# From Render logs, should see:
"Database schema initialized successfully"
```

### Qdrant Connection Failed

**Error**: `Failed to connect to Qdrant`

**Fix**:
1. Verify `QDRANT_URL` in environment variables
2. Check `QDRANT_API_KEY` is correct
3. Ensure Qdrant cluster is running (check Qdrant Cloud dashboard)

### OpenRouter API Key Invalid

**Error**: `Invalid API key for OpenRouter`

**Fix**:
1. Regenerate API key: https://openrouter.io/keys
2. Update in Render dashboard (Environment tab)
3. Redeploy service

---

## Monitoring & Logs

### Real-Time Logs

```bash
# In Render Dashboard:
1. Select service
2. Click "Logs" tab
3. View live stream
```

### Common Log Patterns

**Healthy Startup**:
```
2025-12-30 18:00:00 - main - INFO - BookRAGAgent starting up...
2025-12-30 18:00:10 - main - INFO - Database initialized
2025-12-30 18:00:15 - main - INFO - RAG agent initialized
2025-12-30 18:00:16 - main - INFO - Dependencies injected
INFO:     Application startup complete.
```

**Request Processing**:
```
2025-12-30 18:05:23 - api.routes - INFO - Chat request from session xxx
2025-12-30 18:05:24 - rag.retrieval - INFO - Searching Qdrant for 5 chunks
2025-12-30 18:05:25 - rag.grounding - INFO - Synthesizing answer
```

### Performance Monitoring

Check Render metrics:
1. Select service
2. Click "Metrics" tab
3. Monitor:
   - CPU usage
   - Memory usage
   - Response time
   - Error rate

---

## Rollback Procedures

### Rollback to Previous Deployment

1. Go to Render Dashboard
2. Select "bookrag-api" service
3. Click "Deployments" tab
4. Find previous successful deployment
5. Click "Redeploy" on that version

**Time**: Usually < 1 minute

### Manual Rollback

If previous deployment not available:

```bash
# Option 1: Revert code changes
git revert <commit-hash>
git push origin main
# Render auto-deploys from main

# Option 2: Manual restart (keeps current code)
# In Render Dashboard → Service → "Manual Deploy" → "Deploy latest"
```

### Zero-Downtime Deployment

Render handles zero-downtime automatically:
1. New instance starts
2. Health checks verify readiness
3. Traffic switches when ready
4. Old instance shuts down

---

## Performance Optimization

### Reduce Build Time

1. Use `.dockerignore` (already configured)
2. Layer caching: requirements first, then code
3. Multi-stage builds (optional for smaller images)

### Reduce Runtime Memory

- Current: ~512MB (Starter plan)
- Upgrade if needed: Standard plan → 1GB

### Connection Pooling

Database connections are pooled automatically by SQLAlchemy.

### Caching

Qdrant caches frequently accessed vectors.

---

## Security Checklist

- ✅ `.env` NOT committed to Git
- ✅ Non-root user in Docker (appuser)
- ✅ Environment variables set in Render, not image
- ✅ Database password NOT in Dockerfile
- ✅ API keys NOT in logs
- ✅ HTTPS enforced by Render
- ✅ Health check endpoint public (safe)

---

## Support & Issues

### Debug Mode

Add to environment variables (temporary):
```
LOG_LEVEL=DEBUG
```

Then check logs for detailed output.

### Common Commands

```bash
# Pull latest code
git pull origin main

# Deploy
# (Automatic on push to main, or manual in Render)

# Check status
# Render Dashboard → Logs tab

# View deployment history
# Render Dashboard → Deployments tab
```

### Getting Help

1. Check logs in Render Dashboard
2. Review error messages
3. Try manual redeploy
4. Check this guide for your error
5. Refer to README.md
6. Open GitHub issue with error details

---

## Appendix: File Locations

| File | Purpose |
|------|---------|
| `Dockerfile` | Docker image definition |
| `.dockerignore` | Exclude files from build |
| `render.yaml` | Render configuration (optional) |
| `backend/requirements.txt` | Python dependencies |
| `backend/main.py` | FastAPI entry point |
| `.env.example` | Example environment variables |
| `README.md` | Project README |
| `DEPLOYMENT.md` | This file |

---

**Last Updated**: 2025-12-30
**Version**: 1.0
