# Deploy RAG Backend to Render.com - Step-by-Step Guide

## Prerequisites Checklist
- [ ] GitHub account with your repo
- [ ] Render.com account (free)
- [ ] All API credentials rotated and updated in local `.env`:
  - [ ] OPENAI_API_KEY (new)
  - [ ] DATABASE_URL (Neon - new)
  - [ ] QDRANT_URL + QDRANT_API_KEY (Qdrant - new)
  - [ ] GROQ_API_KEY (new)
  - [ ] COHERE_API_KEY (new if using)
  - [ ] GEMINI_API_KEY (new if using)
  - [ ] HUGGINGFACE_API_TOKEN (new if using)

---

## Step 1: Connect GitHub to Render

### 1.1 Sign In / Sign Up
1. Go to **https://render.com**
2. Click **"Sign up"** or **"Log in"**
3. Choose **"GitHub"** (or authenticate with email)
4. If first time: Click "Authorize render" to give Render access to your repositories

### 1.2 Authorize Repository Access
- You'll be asked to authorize `render-io` GitHub app
- Click **"Authorize render-io"**
- Select "All repositories" or just your repo

✅ **Status**: GitHub connected to Render

---

## Step 2: Create New Web Service on Render

### 2.1 Navigate to Dashboard
1. Click **"Dashboard"** or go to https://dashboard.render.com
2. Click **"New +"** button (top right)
3. Select **"Web Service"**

### 2.2 Connect Repository
1. **Search for repository**: Find `Physical-AI--humanoid-robotics-book` (or your repo name)
2. Click **"Connect"**
3. You'll see a connection dialog

### 2.3 Select Branch
- **Branch**: `feature/2-rag-chatbot-integration` (or your current branch)
- Click **"Deploy"** (it may say "Create" first)

✅ **Status**: Repository connected to Render

---

## Step 3: Configure Service Settings

### 3.1 Basic Settings
Fill in these fields on the Render service creation page:

| Field | Value |
|-------|-------|
| Name | `rag-chatbot-backend` |
| Environment | `Python 3` |
| Build Command | `cd rag-backend && pip install -r requirements.txt` |
| Start Command | `cd rag-backend && uvicorn src.main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | `Free` |
| Auto-deploy | Toggle **ON** |

### 3.2 Region
- Choose nearest region to your users
- Examples: `Oregon (us-west)`, `Ohio (us-east)`, `Frankfurt (eu-west)`

### 3.3 Click "Advanced" (optional but recommended)
- This lets you add environment variables immediately

✅ **Status**: Service configuration entered

---

## Step 4: Add Environment Variables

**CRITICAL**: Enter these EXACTLY as shown below. Copy-paste from your NEW rotated `.env` file.

### 4.1 Navigate to Environment Variables
1. Click **"Advanced"** section (if not already expanded)
2. Look for **"Environment Variables"** section
3. Click **"Add Environment Variable"** for each line below

### 4.2 Required Environment Variables

Add each variable one by one. Format: **Key = Value**

```
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
QDRANT_COLLECTION_NAME=aibook_chunk
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=500
GROQ_LLM_MODEL=llama-3.1-70b-versatile
COHERE_LLM_MODEL=command
RATE_LIMIT_QUERIES_PER_MINUTE=10
RATE_LIMIT_QUERIES_PER_DAY=1000
SESSION_TIMEOUT_HOURS=24
MAX_SELECTED_TEXT_TOKENS=2000
MAX_SELECTED_TEXT_CHARACTERS=10000
ALLOWED_ORIGINS_STR=https://mehreen676.github.io,https://rag-chatbot-backend.onrender.com,http://localhost:3000,http://localhost:8000
```

### 4.3 Sensitive Environment Variables

**Copy these from your NEW `.env` file:**

```
DATABASE_URL=<paste your NEW Neon connection string>
QDRANT_URL=<paste your Qdrant cluster URL>
QDRANT_API_KEY=<paste your NEW Qdrant API key>
OPENAI_API_KEY=<paste your NEW OpenAI API key>
GROQ_API_KEY=<paste your NEW Groq API key>
COHERE_API_KEY=<paste your NEW Cohere API key>
GEMINI_API_KEY=<paste your NEW Gemini API key>
HUGGINGFACE_API_TOKEN=<paste your NEW HuggingFace token>
SECRET_KEY=<generate new: python -c "import secrets; print(secrets.token_urlsafe(32))">
```

### 4.4 Instructions for Each Variable

**For each environment variable:**
1. Click **"Add Environment Variable"**
2. Type the **Key** (left side)
3. Type or paste the **Value** (right side)
4. Click outside or press Enter
5. Repeat

**Example for DATABASE_URL:**
```
Key:   DATABASE_URL
Value: postgresql://neondb_owner:PASSWORD@ep-curly-queen-a4lilgi7-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

⚠️ **IMPORTANT**:
- Do NOT use quotes around values
- Do NOT commit these values to git
- Only Render will store these securely

✅ **Status**: All environment variables entered

---

## Step 5: Generate SECRET_KEY

Run this command in your terminal to generate a unique SECRET_KEY:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Example output:
```
xK_f9pL2mN4qR8tV3wX7zY1aB5cD9eF6gH0jK2lM
```

Copy this output and use it as the value for `SECRET_KEY` environment variable.

---

## Step 6: Create Web Service (Deploy!)

### 6.1 Final Review
1. Double-check all settings:
   - [ ] Build command: `cd rag-backend && pip install -r requirements.txt`
   - [ ] Start command: `cd rag-backend && uvicorn src.main:app --host 0.0.0.0 --port $PORT`
   - [ ] All environment variables entered
   - [ ] Branch: `feature/2-rag-chatbot-integration`

### 6.2 Deploy
1. Click **"Create Web Service"** button (bottom right)
2. Render will start deploying immediately
3. You'll see a build log appearing

### 6.3 Monitor Deployment
1. Go to **"Deployments"** tab
2. Watch the build process in real-time
3. You should see:
   - `✓ Cloning repository`
   - `✓ Installing dependencies`
   - `✓ Starting uvicorn`
   - `✓ Deployment successful` (shows service URL)

**Expected time**: 3-5 minutes

✅ **Status**: Web service deployed!

---

## Step 7: Verify Deployment Success

Once you see **"Live ✅"** status:

### 7.1 Check Health Endpoint
Open in your browser or terminal:

```bash
curl https://rag-chatbot-backend.onrender.com/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-18T...",
  "version": "1.0.0",
  "environment": "production"
}
```

### 7.2 View API Documentation
Open in your browser:
```
https://rag-chatbot-backend.onrender.com/docs
```

You should see Swagger UI with all available endpoints.

### 7.3 Test Query Endpoint
The Qdrant collection already has data, so you can test immediately:

```bash
curl -X POST https://rag-chatbot-backend.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is ROS 2?",
    "mode": "full_book"
  }'
```

**Expected response**: JSON with answer and retrieved chunks

### 7.4 Monitor Logs
1. In Render dashboard, click **"Logs"** tab
2. Look for any errors or warnings
3. Common issues:
   - Database connection failed → Check DATABASE_URL
   - Invalid API key → Check OPENAI_API_KEY format
   - Qdrant not found → Check QDRANT_URL and QDRANT_API_KEY

✅ **Status**: Service verified and working!

---

## Troubleshooting

### Build Failed
**Symptoms**: Red X on "Build" step

**Solutions**:
1. Check build logs for error message
2. Verify Python version in runtime.txt
3. Verify all packages in requirements.txt are available
4. Common issue: qdrant-client version (should be 1.16.2)

### Service Won't Start
**Symptoms**: "Deployment failed" or stuck on "Starting"

**Solutions**:
1. Check start command uses `$PORT` (not hardcoded port)
2. Verify ENVIRONMENT=production and DEBUG=false
3. Check logs for Python errors

### Health Check Fails
**Symptoms**: `/health` returns 500 or times out

**Solutions**:
1. Verify all environment variables are set
2. Check DATABASE_URL is accessible
3. Check QDRANT_URL is accessible
4. Review Render logs for connection errors

### Query Returns Empty
**Symptoms**: `/query` returns results but with no chunks

**Solutions**:
1. Verify Qdrant collection `aibook_chunk` has data
2. Check QDRANT_URL and QDRANT_API_KEY are correct
3. Test collection from Qdrant dashboard

### CORS Errors
**Symptoms**: Frontend gets CORS error

**Solutions**:
1. Update ALLOWED_ORIGINS_STR to include your frontend domain
2. Format: `https://example.com,https://another.com`
3. Redeploy after updating

---

## Your Deployed Service URL

Once deployed successfully, your backend will be available at:

```
https://rag-chatbot-backend.onrender.com
```

**API Endpoints**:
- Health: `https://rag-chatbot-backend.onrender.com/health`
- Docs: `https://rag-chatbot-backend.onrender.com/docs`
- Query: `https://rag-chatbot-backend.onrender.com/query` (POST)
- Ingest: `https://rag-chatbot-backend.onrender.com/ingest` (POST)

---

## Important Notes

⚠️ **Free Tier Spin-Down**:
- Service spins down after 15 minutes of inactivity
- Next request will take 30-60 seconds to start (cold start)
- Upgrade to paid plan ($7/month) to keep always-on

⚠️ **Cost**:
- Backend: Free tier
- Embeddings (OpenAI): ~$2-5/month with moderate usage
- Database (Neon): Free tier available
- Vector DB (Qdrant): Free tier available

⚠️ **Auto-Deploy**:
- Service auto-deploys when you push to connected branch
- You can disable in Settings → Auto-deploy if needed

---

## Next Steps

1. ✅ Deploy to Render (THIS GUIDE)
2. 🚀 Update frontend to use new API URL
3. 📊 Monitor service health and costs
4. 🔐 Set up error tracking (Sentry)
5. 📈 Configure performance monitoring

---

## Support

- Render Docs: https://render.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com/
- API Reference: Use `/docs` endpoint on deployed service
- Issues: Check Render logs and service health

---

**Status**: Ready to deploy! ✅

Your code is pushed to GitHub and all configuration files are in place.
